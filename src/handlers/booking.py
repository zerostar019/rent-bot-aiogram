from aiogram import F, Router
from aiogram.types import CallbackQuery
from utils import show_error_callback

booking = Router()


@booking.callback_query(F.data == "booking")
async def begin_booking(callback: CallbackQuery):
    try:
        await callback.answer("В разработке...")
    except Exception as e:
        print(e)
        await show_error_callback(callback=callback)
