from aiogram.types import CallbackQuery, Message
from constants import ERROR_TEXT
from handlers.keyboard.kb import return_to_menu


async def show_error_callback(callback: CallbackQuery) -> None:
    keyboard = await return_to_menu()
    await callback.message.edit_text(text=ERROR_TEXT, reply_markup=keyboard)


async def show_error_message(msg: Message, message: Message) -> None:
    keyboard = await return_to_menu()
    if msg:
        await msg.edit_text(text=ERROR_TEXT, reply_markup=keyboard)
    else:
        await message.answer(text=ERROR_TEXT, reply_markup=keyboard)
