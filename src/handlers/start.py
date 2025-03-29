from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from handlers.keyboard.kb import start_keyboard
from database.database import db

from handlers.booking import booking
from utils import show_error_callback, show_error_message

# Support
from handlers.support import support
from constants import GREETING_TEXT


start = Router()
start.include_routers(support, booking)


@start.message(F.text == "/start")
async def start_bot(message: Message):
    try:
        keyboard = await start_keyboard()
        await db.register_user(user_id=message.chat.id, role="user")
        msg = await message.answer(text=GREETING_TEXT, reply_markup=keyboard)
    except Exception as e:
        await show_error_message(msg=msg, message=message)
        print(e)


@start.callback_query(F.data == "menu")
async def return_to_menu(callback: CallbackQuery):
    try:
        keyboard = await start_keyboard()
        await callback.answer()
        await callback.message.edit_text(text=GREETING_TEXT, reply_markup=keyboard)
    except Exception as e:
        await show_error_callback(callback=callback)
        print(e)
