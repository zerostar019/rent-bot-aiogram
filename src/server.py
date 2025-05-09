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
from datetime import datetime
from text import create_booking_text
from handlers.keyboard.kb import create_finish_booking_kb
from starlette.responses import FileResponse
import os
from fastapi import HTTPException
from fastapi.responses import JSONResponse

# other modules imports
from bot.redis_instance import redis
from bot.bot_instance import bot
from bot.ws import manager
from config import env
from handlers.start import start

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated


from fastapi import UploadFile, File
from typing import List
import shutil
import pathlib


class BookingBody(BaseModel):
    date: datetime
    time: str
    user_id: int
    sum: str


dp = Dispatcher(storage=RedisStorage(redis))
dp.include_router(start)

UPLOAD_DIR = str(pathlib.Path(__file__).resolve().parent) + "/documents/"
BOT_PATH = "/bot_updates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Turn on the bot
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


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    expose_headers=["*"],
    allow_headers=["*"],
)


@app.post(BOT_PATH)
async def process_bot_updates(update: Update):
    # Process the update from TelegramAPI
    bot_update = Update.model_validate(obj=update, context={"bot": bot})
    # Feed update object to bot
    await dp.feed_update(bot=bot, update=bot_update)


@app.websocket("/chat")
async def process_chat_messages(websocket: WebSocket):
    try:
        await manager.connect(websocket=websocket)
        while True:
            data = await websocket.receive_json()
            if "user_id" in data:
                await db.save_message_from_panel(
                    message_text=data["message"], chat_id=int(data["user_id"])
                )
                await bot.send_message(chat_id=data["user_id"], text=data["message"])
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


@app.get("/get-busy")
async def return_busy_dates(datetime_start: str):
    start_date = datetime.fromtimestamp(int(datetime_start))
    busy_dates = await db.get_booked_days(
        date_array=[
            start_date.year,
            start_date.month,
            start_date.day,
            start_date.hour,
            start_date.minute,
        ]
    )
    return JSONResponse({"success": True, "data": busy_dates})


@app.post("/booking")
async def process_booking(
    datetime_start: Annotated[str, Form()],
    datetime_end: Annotated[str, Form()],
    user_id: Annotated[str, Form()],
    amount: Annotated[str, Form()],
):
    try:
        start_date = datetime.fromtimestamp(int(datetime_start))
        end_date = datetime.fromtimestamp(int(datetime_end))
        booking_id = await db.new_rental(
            user_id=int(user_id),
            rent_type="daily",
            time_interval=[
                [start_date.year, start_date.month, start_date.day, 14, 00],
                [end_date.year, end_date.month, end_date.day, 13, 00],
            ],
            amount=int(amount),
        )
        booking_text = await create_booking_text(
            start_time=start_date.strftime("%d.%m.%Y, %H:%M"),
            end_time=end_date.strftime("%d.%m.%Y, %H:%M"),
            amount=amount,
        )
        if booking_id is not None:
            reply_markup = await create_finish_booking_kb(booking_id=booking_id)
            await bot.send_message(
                chat_id=int(user_id), text=booking_text, reply_markup=reply_markup
            )
            return JSONResponse({"success": True, "data": "Rent booked successfully!"})
        return JSONResponse(
            {"success": False, "data": "There is a problem with booking!"}
        )
    except Exception as e:
        print(e)


@app.get("/chat-users")
async def get_users_for_chat():
    try:
        users = await db.get_users_chat()
        return JSONResponse({"success": True, "data": users})
    except Exception as e:
        print(e)
        return JSONResponse({"success": False, "data": "Failed fetch users!"})


@app.get("/user/chat")
async def get_user_chat(user_id: str):
    try:
        messages = await db.get_chat_by_user_id(user_id=int(user_id))
        await db.update_read_at(chat_id=int(user_id))
        return JSONResponse({"success": True, "data": messages})
    except Exception as e:
        print(e)
        return JSONResponse({"success": False, "data": "Failed fetch user chat!"})


@app.get("/get-file")
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


@app.post("/upload/panel")
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
            print(file.content_type)
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
