from fastapi import FastAPI, WebSocket, Form
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
from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from scheduler import scheduler
import random

# other modules imports
from bot.redis_instance import redis
from bot.bot_instance import bot
from bot.ws import manager
from config import env
from handlers.start import start
from handlers.keyboard.kb import create_finish_booking_kb
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated


from fastapi import UploadFile, File
from typing import List
import shutil
import pathlib
from aiogram.fsm.strategy import FSMStrategy


class BookingBody(BaseModel):
    date: datetime
    time: str
    user_id: int
    sum: str


dp = Dispatcher(storage=RedisStorage(redis), fsm_strategy=FSMStrategy.USER_IN_CHAT)
dp.include_router(start)

UPLOAD_DIR = str(pathlib.Path(__file__).resolve().parent) + "/documents/"
BOT_PATH = "/bot_updates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Turn on the bot
    scheduler.start()
    await db.connect()
    await bot.set_webhook(
        url=str(env.HOST.get_secret_value()) + BOT_PATH,
        allowed_updates=["callback_query", "message"],
        drop_pending_updates=True,
    )
    yield

    # Turn off the bot
    await bot.session.close()
    await db.close()
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    expose_headers=["*"],
    allow_headers=["*"],
)


@app.post("/app" + BOT_PATH)
async def process_bot_updates(update: Update):
    # Process the update from TelegramAPI
    bot_update = Update.model_validate(obj=update, context={"bot": bot})
    # Feed update object to bot
    await dp.feed_update(bot=bot, update=bot_update)


@app.websocket("/app/chat")
async def process_chat_messages(websocket: WebSocket):
    try:
        await manager.connect(websocket=websocket)
        while True:
            data = await websocket.receive_json()
            if "user_id" in data:
                await db.save_message_from_panel(
                    message_text=data["message"], chat_id=int(data["user_id"])
                )
                text = "<b>Администратор:</b>\n\n"
                text += data["message"]
                await bot.send_message(
                    chat_id=data["user_id"], text=text, parse_mode="HTML"
                )
    except TelegramForbiddenError as e:
        print("Вы были заблокированы в боте!", e)
        message = await db.save_message_from_bot(
            message_text="Пользователь заблокировал бота!", user_id=data["user_id"]
        )
        await manager.broadcast(data=message)
        return
    except Exception as e:
        print(e)
    finally:
        await manager.disconnect(websocket=websocket)


@app.get("/app/get-busy")
async def return_busy_dates(datetime_start: str, isSecondInterval: bool = False):
    try:
        start_date = datetime.fromtimestamp(int(datetime_start))
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
        return JSONResponse({"success": True, "data": busy_dates})
    except Exception as e:
        print(f"Error fetching busy dates: {e}")
        return HTTPException(status_code=500, detail="Internal server error")


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
        if user_id == "":
            booking_text += "\n\nБронирование было произведено администратором, оплата не требуется!"
            admins = await db.get_admins()
            user_id = random.choice(admins)
            reply_markup = None

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

        if booking_id is not None:
            reply_markup = await create_finish_booking_kb(booking_id=booking_id)
            run_date = datetime.now() + timedelta(minutes=20)
            job_args = (booking_id, user_id)
            job = scheduler.add_job(
                send_deny_message,
                "date",
                run_date=run_date,
                args=job_args,
                id=f"{user_id}_job",
            )
            print(job)
            if user_id == "":
                reply_markup = None
                job.remove()
            if notification is True:
                await bot.send_message(
                    chat_id=int(user_id), text=booking_text, reply_markup=reply_markup
                )
            return JSONResponse({"success": True, "data": "Rent booked successfully!"})
        return JSONResponse(
            {"success": False, "data": "There is a problem with booking!"}
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            {"success": False, "data": "There is a problem with booking!"}
        )


@app.get("/app/chat-users")
async def get_users_for_chat():
    try:
        users = await db.get_users_chat()
        return JSONResponse({"success": True, "data": users})
    except Exception as e:
        print(e)
        return JSONResponse({"success": False, "data": "Failed fetch users!"})


@app.get("/app/user/chat")
async def get_user_chat(user_id: str):
    try:
        messages = await db.get_chat_by_user_id(user_id=int(user_id))
        await db.update_read_at(chat_id=int(user_id))
        return JSONResponse({"success": True, "data": messages})
    except Exception as e:
        print(e)
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
        print(f"Error fetching file: {e}")
        return HTTPException(status_code=500, detail="Internal server error")


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
            if file.content_type.startswith("image") and not file.content_type.find(
                "svg"
            ):
                photos.append(UPLOAD_DIR + file.filename)
            else:
                documents.append(UPLOAD_DIR + file.filename)

            file_path = os.path.join(UPLOAD_DIR, file.filename)
            # Сохранение файла в папку
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            text = ""
            if message_text != "empty":
                text = message_text

            result = await db.save_file_from_bot(
                file_name=file.filename,
                file_path=file_path,
                user_id=111,
                chat_id=user_id,
                message_text=text,
            )
            # Сохранение в БД
            if files[0] != file:
                result = await db.save_file_from_bot(
                    file_name=file.filename,
                    file_path=file_path,
                    user_id=111,
                    chat_id=user_id,
                    message_text="",
                )

            results.append(result)
        caption_text = None
        if message_text != "empty":
            caption_text = message_text
        if len(photos) > 0:
            media_group = MediaGroupBuilder(caption=caption_text)
            for photo in photos:
                media_group.add_photo(FSInputFile(photo))
            await bot.send_media_group(media=media_group.build(), chat_id=user_id)

        if len(documents) > 0:
            media_group = MediaGroupBuilder(caption=caption_text)
            for document in documents:
                media_group.add_document(FSInputFile(document))
            await bot.send_media_group(media=media_group.build(), chat_id=user_id)

        return JSONResponse(
            {
                "success": True,
                "message": f"{len(files)} файлов успешно загружены",
                "data": results,
            }
        )

    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500, content={"success": False, "message": f"Ошибка: {str(e)}"}
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

    bookings_data = await db.get_bookings(
        select_base=select_base,
        limit_offset=limit_offset,
        count_query=count_query,
        params=params,
    )

    bookings_data.update({"page": page, "per_page": per_page})
    return JSONResponse({"success": True, "data": bookings_data})


@app.get("/app/get-booking")
async def get_booking_by_id(booking_id: int):
    try:
        booking_data = await db.get_booking_data_by_id(booking_id=booking_id)
        if booking_data is not None:
            return JSONResponse({"success": True, "data": booking_data})
        return JSONResponse({"success": False, "data": None})
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500, content={"success": False, "message": f"Ошибка: {str(e)}"}
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
        approved = bool(approved.capitalize())
        result = await db.update_rental(
            id_rental=id_rental,
            user_id=int(user_id),
            rent_type=rent_type,
            time_interval=time_interval,
            amount=int(amount),
            approved=approved,
        )

        if result is not None:
            return JSONResponse(
                {"success": True, "data": "Successfully updated the rental!"}
            )

        return JSONResponse(
            {"sucess": False, "data": "Error while trying to update rental!"}
        )

    except Exception as e:
        print(e)
        return JSONResponse(
            {"success": False, "data": "There is a problem with updating a booking!"}
        )


@app.post("/app/update-rental-status")
async def update_rental_status(
    approved: Annotated[str, Form()],
    id_rental: Annotated[int, Form()],
):
    try:
        if approved.strip() == "false":
            approved = False
        elif approved.strip() == "true":
            approved = True
        result = await db.update_rental_status(
            id_rental=int(id_rental), approved=approved
        )
        text = "✅ Бронирование подтверждено!"
        await db.delete_booking_by_id(booking_id=int(id_rental))
        if approved is False:
            text = "❌ Бронирование отклонено"
        if result is not None:
            await bot.send_message(text=text, chat_id=result["id_user"])
            return JSONResponse(
                {"success": True, "data": "Rental status updated successfully!"}
            )
        return JSONResponse({"success": False, "data": "Rental status not updated!"})
    except Exception as e:
        print(e)
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
        if is_deleted is True:
            return JSONResponse({"success": True, "data": ""})
        return JSONResponse({"success": False, "data": None})
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500, content={"success": False, "message": f"Ошибка: {str(e)}"}
        )


@app.get("/app/get-field-text")
async def get_payment_text(field_name: str) -> JSONResponse:
    try:
        payment_text = await db.get_field_text(field_name=field_name)
        answer = {"text": payment_text}
        return JSONResponse({"success": True, "data": answer})
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500, content={"success": False, "message": f"Ошибка: {str(e)}"}
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
        print(e)
        return JSONResponse(
            status_code=500, content={"success": False, "message": f"Ошибка: {str(e)}"}
        )


async def send_deny_message(booking_id: int, chat_id: int):
    try:
        booking_data = await db.get_booking_data_by_id(booking_id=booking_id)
        if booking_data["approved"] is False:
            await db.delete_booking_by_id(booking_id=booking_id)
            await bot.send_message(
                chat_id=chat_id,
                text="ℹ️ Истекло время оплаты!\n\nК сожалению, бронирование отменено!",
            )
            return
    except Exception as e:
        print(e)
