from fastapi import FastAPI
from contextlib import asynccontextmanager

# aiogram imports
from aiogram import Dispatcher
from aiogram.types import Update
from aiogram.fsm.storage.redis import RedisStorage


# other modules imports
from bot.redis_instance import redis
from bot.bot_instance import bot
from config import env
from handlers.start import start

from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class BookingBody(BaseModel):
    date: datetime
    time: str
    user_id: int
    sum: str


dp = Dispatcher(storage=RedisStorage(redis))
dp.include_router(start)


BOT_PATH = "/bot_updates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Turn on the bot
    await bot.set_webhook(
        url=str(env.HOST.get_secret_value()) + BOT_PATH,
        allowed_updates=["callback_query", "message"],
        drop_pending_updates=True,
    )
    yield

    # Turn off the bot
    await bot.session.close()


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
