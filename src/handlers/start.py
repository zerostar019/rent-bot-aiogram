from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from handlers.keyboard.kb import start_keyboard, admin_keyboard
from database.psql_db import db
from aiogram.fsm.context import FSMContext
from bot.redis_instance import redis

from handlers.booking import booking
from utils import show_error_callback, show_error_message

# Support
from handlers.support import support
from constants import GREETING_TEXT


start = Router()
start.include_routers(booking, support)


@start.message(F.text == "/start")
async def start_bot(message: Message, state: FSMContext):
    try:
        admins = await db.get_admins()
        await state.clear()
        keyboard = await start_keyboard()
        if message.chat.id in admins:
            keyboard = await admin_keyboard()
        is_registered = await db.check_user_registered(telegram_id=message.chat.id)
        if is_registered is None:
            await db.register_user(telegram_id=message.chat.id)
            if await redis.exists("chat_users"):
                await redis.delete("chat_users")
        msg = await message.answer(text=GREETING_TEXT, reply_markup=keyboard)
    except Exception as e:
        await show_error_message(msg=msg, message=message)
        print(e)


@start.callback_query(F.data == "menu")
async def return_to_menu(callback: CallbackQuery, state: FSMContext):
    try:
        await state.clear()
        keyboard = await start_keyboard()
        await callback.answer()
        await callback.message.edit_text(text=GREETING_TEXT, reply_markup=keyboard)
    except Exception as e:
        await show_error_callback(callback=callback)
        print(e)
