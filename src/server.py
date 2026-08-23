from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form, Request, HTTPException, Query
from contextlib import asynccontextmanager

# aiogram imports
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import FSInputFile
from aiogram import Dispatcher
from aiogram.types import Update
from aiogram.exceptions import TelegramForbiddenError
from aiogram.fsm.storage.redis import RedisStorage
from database.psql_db import db
from datetime import datetime, timedelta
from text import create_booking_text
from starlette.responses import FileResponse
import os
from fastapi.responses import JSONResponse
from typing import Optional
from scheduler import scheduler
import random
import uuid

# other modules imports
from bot.redis_instance import redis
from bot import cache
from bot.bot_instance import create_bot, get_bot
from bot.ws import manager
from config import env
from handlers.start import start
from handlers.keyboard.kb import create_finish_booking_kb
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import Annotated


from fastapi import UploadFile, File
from typing import List
import shutil
import pathlib
from aiogram.fsm.strategy import FSMStrategy
from utils import escape_html, notify_admin_error
import logging

logger = logging.getLogger(__name__)


class BookingBody(BaseModel):
    date: datetime
    time: str
    user_id: int
    sum: str


dp = Dispatcher(storage=RedisStorage(redis), fsm_strategy=FSMStrategy.USER_IN_CHAT)
dp.include_router(start)

UPLOAD_DIR = str(pathlib.Path(__file__).resolve().parent) + "/documents/"
BOT_PATH = "/bot_updates"


def safe_filename(filename: str) -> str:
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    return "".join(c for c in filename if c in keep)


def unique_filename(filename: str) -> str:
    """Добавляет короткий суффикс, чтобы файлы с одинаковым именем
    не затирали друг друга в общей папке documents."""
    safe = safe_filename(filename) or "file"
    stem, dot, ext = safe.rpartition(".")
    if not dot:
        stem, ext = safe, ""
    suffix = uuid.uuid4().hex[:8]
    return f"{stem}_{suffix}{'.' + ext if ext else ''}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Turn on the bot
    await create_bot()
    scheduler.start()
    await db.connect()
    # secret_token заставляет Telegram присылать заголовок
    # X-Telegram-Bot-Api-Secret-Token. Без него эндпоинт вебхука публичный:
    # любой мог отправить туда поддельный Update от имени чужого user_id.
    await get_bot().set_webhook(
        url=str(env.HOST.get_secret_value()) + BOT_PATH,
        allowed_updates=["callback_query", "message"],
        drop_pending_updates=True,
        secret_token=(
            env.WEBHOOK_SECRET.get_secret_value()
            if env.WEBHOOK_SECRET is not None
            else None
        ),
    )
    yield

    # Turn off the bot
    await get_bot().session.close()
    await db.close()
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

CORS_ORIGINS = [
    "https://businesspochta.kazan.hlab.kz",
    "http://localhost:8083",
    "http://localhost:8084",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    expose_headers=["*"],
    allow_headers=["*"],
)


@app.post("/app" + BOT_PATH)
async def process_bot_updates(request: Request):
    # 1. Проверка подлинности. Чужой запрос отбрасываем молча:
    #    эндпоинт открыт в интернет и его постоянно сканируют.
    if env.WEBHOOK_SECRET is not None:
        provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if provided != env.WEBHOOK_SECRET.get_secret_value():
            logger.warning(
                "Отклонён webhook без валидного секрета (client=%s)",
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(status_code=403, content={"ok": False})

    # 2. Разбор тела. Некорректный payload — это мусор от сканеров,
    #    а не сбой бота, поэтому логируем, но не шлём админу в Telegram
    #    (иначе каждый мусорный POST превращается в уведомление).
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"ok": False})

    try:
        bot = get_bot()
        update = Update.model_validate(payload, context={"bot": bot})
    except ValidationError as e:
        logger.warning("Некорректный Update в вебхуке: %s", e)
        return JSONResponse(status_code=400, content={"ok": False})

    # 3. Ошибка уже внутри обработки апдейта — настоящая проблема бота.
    try:
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        await notify_admin_error(e, "process_bot_updates")
    return JSONResponse({"ok": True})


@app.websocket("/app/chat")
async def process_chat_messages(websocket: WebSocket):
    try:
        await manager.connect(websocket=websocket)
        while True:
            data = await websocket.receive_json()
            if "user_id" not in data:
                continue
            # Ошибка по одному адресату не должна рвать сокет панели целиком:
            # раньше любой заблокировавший бота пользователь закрывал админу чат.
            try:
                chat_id = int(data["user_id"])
                admin_text = str(data.get("message", ""))
                message = await db.save_message_from_panel(
                    message_text=admin_text, chat_id=chat_id
                )
                await manager.broadcast(data=message)
                text = "<b>Администратор:</b>\n\n" + escape_html(admin_text)
                await get_bot().send_message(
                    chat_id=chat_id, text=text, parse_mode="HTML"
                )
            except TelegramForbiddenError as e:
                await notify_admin_error(
                    e, "WebSocket: пользователь заблокировал бота"
                )
                blocked = await db.save_message_from_bot(
                    message_text="Пользователь заблокировал бота!",
                    user_id=int(data["user_id"]),
                )
                await manager.broadcast(data=blocked)
            except Exception as e:
                await notify_admin_error(e, "WebSocket: отправка сообщения")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await notify_admin_error(e, "WebSocket process_chat_messages")
    finally:
        await manager.disconnect(websocket=websocket)


@app.get("/app/get-busy")
async def return_busy_dates(datetime_start: str, isSecondInterval: bool = False):
    try:
        # Фронт присылает значение с пробельным паддингом (?datetime_start=%20%201787342400),
        # поэтому нормализуем перед разбором.
        start_date = datetime.fromtimestamp(int(datetime_start.strip()))
        scope = "blocked" if isSecondInterval else "booked"
        cache_key = str(int(start_date.timestamp()))

        cached = await cache.get_busy(scope, cache_key)
        if cached is not None:
            return JSONResponse({"success": True, "data": cached})

        busy_dates = []
        if isSecondInterval is False:
            busy_dates = await db.get_booked_days(
                date_array=[
                    start_date.year,
                    start_date.month,
                    start_date.day,
                    start_date.hour,
                    start_date.minute,
                ]
            )
        if isSecondInterval is True:
            busy_dates = await db.get_blocked_days(
                [
                    start_date.year,
                    start_date.month,
                    start_date.day,
                    start_date.hour,
                    start_date.minute,
                ]
            )
        await cache.set_busy(scope, cache_key, busy_dates)
        return JSONResponse({"success": True, "data": busy_dates})
    except Exception as e:
        await notify_admin_error(e, "return_busy_dates")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/app/booking")
async def process_booking(
    datetime_start: Annotated[str, Form()],
    datetime_end: Annotated[str, Form()],
    amount: Annotated[str, Form()],
    notification: Annotated[Optional[bool], Form()] = True,
    from_panel: Annotated[Optional[bool], Form()] = False,
    user_id: Annotated[Optional[str], Form()] = "",
):
    try:
        start_date = datetime.fromtimestamp(int(datetime_start))
        end_date = datetime.fromtimestamp(int(datetime_end))
        booking_text = await create_booking_text(
            start_time=start_date.strftime("%d.%m.%Y, %H:%M"),
            end_time=end_date.strftime("%d.%m.%Y, %H:%M"),
            amount=amount,
        )
        # user_id ниже перезаписывается на админа, поэтому запоминаем признак
        # отдельно — иначе проверки "user_id == \"\"" после присваивания мертвы.
        is_admin_booking = user_id == ""
        if is_admin_booking:
            booking_text += "\n\nБронирование было произведено администратором, оплата не требуется!"
            admins = await db.get_admins()
            if not admins:
                return JSONResponse(
                    {"success": False, "data": "There are no admins to assign booking!"}
                )
            user_id = random.choice(admins)

        booking_id = await db.new_rental(
            user_id=int(user_id),
            rent_type="daily",
            time_interval=[
                [start_date.year, start_date.month, start_date.day, 14, 00],
                [end_date.year, end_date.month, end_date.day, 13, 00],
            ],
            amount=int(amount),
            from_panel=from_panel,
        )
        await cache.invalidate()

        if booking_id is not None:
            reply_markup = None
            if not is_admin_booking:
                reply_markup = await create_finish_booking_kb(booking_id=booking_id)
                run_date = datetime.now() + timedelta(minutes=20)
                # id завязан на бронь, а не на пользователя: раньше вторая бронь
                # того же юзера за 20 минут падала с ConflictingIdError.
                scheduler.add_job(
                    send_deny_message,
                    "date",
                    run_date=run_date,
                    args=(booking_id, user_id),
                    id=f"booking_{booking_id}_deny",
                    replace_existing=True,
                )
            if notification is True and not is_admin_booking:
                await get_bot().send_message(
                    chat_id=int(user_id), text=booking_text, reply_markup=reply_markup
                )
            return JSONResponse({"success": True, "data": "Rent booked successfully!"})
        return JSONResponse(
            {"success": False, "data": "There is a problem with booking!"}
        )
    except Exception as e:
        await notify_admin_error(e, "process_booking")
        return JSONResponse(
            {"success": False, "data": "There is a problem with booking!"}
        )


@app.get("/app/chat-users")
async def get_users_for_chat():
    try:
        users = await db.get_users_chat()
        return JSONResponse({"success": True, "data": users})
    except Exception as e:
        await notify_admin_error(e, "get_users_for_chat")
        return JSONResponse({"success": False, "data": "Failed fetch users!"})


@app.get("/app/user/chat")
async def get_user_chat(user_id: str):
    try:
        messages = await db.get_chat_by_user_id(user_id=int(user_id))
        await db.update_read_at(chat_id=int(user_id))
        return JSONResponse({"success": True, "data": messages})
    except Exception as e:
        await notify_admin_error(e, "get_user_chat")
        return JSONResponse({"success": False, "data": "Failed fetch user chat!"})


@app.get("/app/get-file")
async def get_file(file_id: str):
    try:
        file_path = await db.get_file_path(file_id=int(file_id))

        if not file_path or not os.path.exists(file_path["file_path"]):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=file_path["file_path"],
            filename=file_path["file_name"],
        )
    except Exception as e:
        await notify_admin_error(e, "get_file")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/app/upload/panel")
async def upload_files(
    files: List[UploadFile] = File(...),
    user_id: int = Form(...),
    message_text: str = Form(...),
):
    try:
        results = []
        photos = []
        documents = []
        for file in files:
            safe_name = unique_filename(file.filename or "file")
            file_path = os.path.join(UPLOAD_DIR, safe_name)

            content_type = file.content_type or ""
            if content_type.startswith("image") and "svg" not in content_type:
                photos.append(file_path)
            else:
                documents.append(file_path)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            text = ""
            if message_text != "empty":
                text = message_text

            # Подпись прикрепляем только к первому файлу, остальные идут без неё.
            # Раньше здесь был второй save_file_from_bot, из-за чего каждый файл
            # кроме первого попадал в чат дважды.
            result = await db.save_file_from_bot(
                file_name=safe_name,
                file_path=file_path,
                user_id=111,
                chat_id=user_id,
                message_text=text if file is files[0] else "",
            )

            results.append(result)
        caption_text = None
        if message_text != "empty":
            caption_text = message_text
        if len(photos) > 0:
            media_group = MediaGroupBuilder(caption=caption_text)
            for photo in photos:
                media_group.add_photo(FSInputFile(photo))
            await get_bot().send_media_group(media=media_group.build(), chat_id=user_id)

        if len(documents) > 0:
            media_group = MediaGroupBuilder(caption=caption_text)
            for document in documents:
                media_group.add_document(FSInputFile(document))
            await get_bot().send_media_group(media=media_group.build(), chat_id=user_id)

        return JSONResponse(
            {
                "success": True,
                "message": f"{len(files)} файлов успешно загружены",
                "data": results,
            }
        )

    except Exception as e:
        await notify_admin_error(e, "upload_files panel")
        return JSONResponse(
            status_code=500, content={"success": False, "message": "Внутренняя ошибка сервера"}
        )


@app.get("/app/bookings")
async def get_rentals(
    time_interval: Optional[str] = Query(
        None,
        description="Формат: 'от,до' | 'от' | 'до'. Пример: '2024-04-01T00:00:00,2024-04-10T23:59:59'",
    ),
    amount_from: Optional[float] = Query(None, ge=0, description="Минимальная сумма"),
    amount_to: Optional[float] = Query(None, ge=0, description="Максимальная сумма"),
    per_page: int = 10,
    page: int = 1,
    approved: Optional[bool] = False,
):
    # Валидация параметров
    if per_page < 1:
        raise HTTPException(status_code=400, detail="per_page must be at least 1")
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be at least 1")
    if amount_from is not None and amount_to is not None and amount_from > amount_to:
        raise HTTPException(
            status_code=400, detail="amount_from не может быть больше amount_to"
        )

    conditions = []
    params = []

    # Парсинг time_interval
    if time_interval:
        parts = [x.strip() for x in time_interval.split(",")]
        if len(parts) > 2:
            raise HTTPException(
                status_code=400,
                detail="time_interval должен быть в формате 'от,до', 'от' или 'до'",
            )
        try:
            from datetime import datetime

            start = datetime.fromisoformat(parts[0]) if parts[0] else None
            end = (
                datetime.fromisoformat(parts[1])
                if len(parts) == 2 and parts[1]
                else None
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Неверный формат даты. Используйте ISO 8601, например: 2024-04-01T12:00:00",
            )
        if start and end and start > end:
            raise HTTPException(
                status_code=400, detail="Начало должно быть раньше окончания"
            )

        if start and end:
            conditions.append(
                f"time_interval && tsrange(${len(params) + 1}, ${len(params) + 2}, '[]')"
            )
            params.extend([start, end])
        elif start:
            conditions.append(f"lower(time_interval) >= ${len(params) + 1}")
            params.append(start)
        elif end:
            conditions.append(f"upper(time_interval) <= ${len(params) + 1}")
            params.append(end)

    # Фильтрация по amount_from и amount_to
    if amount_from is not None:
        conditions.append(f"amount >= ${len(params) + 1}")
        params.append(amount_from)
    if amount_to is not None:
        conditions.append(f"amount <= ${len(params) + 1}")
        params.append(amount_to)

    # Фильтрация по approved
    if approved is not None:
        conditions.append(f"approved = ${len(params) + 1}")
        params.append(approved)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Пагинация
    params.extend([per_page, (page - 1) * per_page])
    limit_offset = f" LIMIT ${len(params) - 1} OFFSET ${len(params)}"

    # SQL-запросы
    select_base = f"SELECT * FROM rental WHERE {where_clause} ORDER BY created_at DESC"
    count_query = f"SELECT COUNT(*) FROM rental WHERE {where_clause}"

    try:
        bookings_data = await db.get_bookings(
            select_base=select_base,
            limit_offset=limit_offset,
            count_query=count_query,
            params=params,
        )
        if bookings_data is None:
            raise RuntimeError("get_bookings вернул None")
        bookings_data.update({"page": page, "per_page": per_page})
        return JSONResponse({"success": True, "data": bookings_data})
    except HTTPException:
        raise
    except Exception as e:
        await notify_admin_error(e, "get_rentals")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Внутренняя ошибка сервера"},
        )


@app.get("/app/get-booking")
async def get_booking_by_id(booking_id: int):
    try:
        booking_data = await db.get_booking_data_by_id(booking_id=booking_id)
        if booking_data is not None:
            return JSONResponse({"success": True, "data": booking_data})
        return JSONResponse({"success": False, "data": None})
    except Exception as e:
        await notify_admin_error(e, "get_booking_by_id")
        return JSONResponse(
            status_code=500, content={"success": False, "message": "Внутренняя ошибка сервера"}
        )


@app.post("/app/update-rental")
async def update_rental(
    datetime_start: Annotated[str, Form()],
    datetime_end: Annotated[str, Form()],
    user_id: Annotated[str, Form()],
    amount: Annotated[str, Form()],
    approved: Annotated[str, Form()],
    id_rental: Annotated[int, Form()],
    rent_type: Annotated[str, Form()],
):
    try:
        start_date = datetime.fromtimestamp(int(datetime_start))
        end_date = datetime.fromtimestamp(int(datetime_end))
        time_interval = [
            [start_date.year, start_date.month, start_date.day, 14, 00],
            [end_date.year, end_date.month, end_date.day, 13, 00],
        ]
        approved = str(approved).strip().lower() in ("true", "1", "yes", "on")
        result = await db.update_rental(
            id_rental=id_rental,
            user_id=int(user_id),
            rent_type=rent_type,
            time_interval=time_interval,
            amount=int(amount),
            approved=approved,
        )
        await cache.invalidate()

        if result is not None:
            return JSONResponse(
                {"success": True, "data": "Successfully updated the rental!"}
            )

        return JSONResponse(
            {"success": False, "data": "Error while trying to update rental!"}
        )

    except Exception as e:
        await notify_admin_error(e, "update_rental")
        return JSONResponse(
            {"success": False, "data": "There is a problem with updating a booking!"}
        )


@app.post("/app/update-rental-status")
async def update_rental_status(
    approved: Annotated[str, Form()],
    id_rental: Annotated[int, Form()],
):
    try:
        approved = str(approved).strip().lower() in ("true", "1", "yes", "on")
        result = await db.update_rental_status(
            id_rental=int(id_rental), approved=approved
        )
        await cache.invalidate()
        text = "✅ Бронирование подтверждено!"
        if approved is False:
            await db.delete_booking_by_id(booking_id=int(id_rental))
            text = "❌ Бронирование отклонено"
        if result is not None:
            await get_bot().send_message(text=text, chat_id=result["id_user"])
            return JSONResponse(
                {"success": True, "data": "Rental status updated successfully!"}
            )
        return JSONResponse({"success": False, "data": "Rental status not updated!"})
    except Exception as e:
        await notify_admin_error(e, "update_rental_status")
        return JSONResponse(
            {
                "success": False,
                "data": "There is a problem with updating a booking status!",
            }
        )


@app.get("/app/delete-booking")
async def delete_booking(booking_id: int) -> JSONResponse:
    try:
        is_deleted = await db.delete_booking_by_id(booking_id=booking_id)
        await cache.invalidate()
        if is_deleted is True:
            return JSONResponse({"success": True, "data": ""})
        return JSONResponse({"success": False, "data": None})
    except Exception as e:
        await notify_admin_error(e, "delete_booking")
        return JSONResponse(
            status_code=500, content={"success": False, "message": "Внутренняя ошибка сервера"}
        )


@app.get("/app/get-field-text")
async def get_payment_text(field_name: str) -> JSONResponse:
    try:
        payment_text = await db.get_field_text(field_name=field_name)
        answer = {"text": payment_text}
        return JSONResponse({"success": True, "data": answer})
    except Exception as e:
        await notify_admin_error(e, "get_payment_text")
        return JSONResponse(
            status_code=500, content={"success": False, "message": "Внутренняя ошибка сервера"}
        )


@app.post("/app/set-field-text")
async def set_field_text(
    field_name: Annotated[str, Form()], field_text: Annotated[str, Form()]
) -> JSONResponse:
    try:
        is_changed = await db.update_field_text(
            field_name=field_name, field_text=field_text
        )
        print(is_changed)
        if is_changed is True:
            return JSONResponse({"success": True, "data": ""})
        return JSONResponse({"success": False, "data": ""})
    except Exception as e:
        await notify_admin_error(e, "set_field_text")
        return JSONResponse(
            status_code=500, content={"success": False, "message": "Внутренняя ошибка сервера"}
        )


async def send_deny_message(booking_id: int, chat_id: int):
    try:
        booking_data = await db.get_booking_data_by_id(booking_id=booking_id)
        if booking_data is None:
            return
        if booking_data["approved"] is False:
            await db.delete_booking_by_id(booking_id=booking_id)
            await cache.invalidate()
            await get_bot().send_message(
                chat_id=chat_id,
                text="ℹ️ Истекло время оплаты!\n\nК сожалению, бронирование отменено!",
            )
    except Exception as e:
        await notify_admin_error(e, f"send_deny_message booking_id={booking_id}")
