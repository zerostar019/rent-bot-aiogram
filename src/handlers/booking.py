from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from utils import show_error_callback
from database.psql_db import db
from handlers.keyboard.kb import attach_bill_kb
from text import create_payment_text, BILL_ATTACH_TEXT
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import pathlib
from bot.bot_instance import bot

PATH_TO_DOCUMENTS = str(pathlib.Path(__file__).resolve().parent.parent) + "/documents/"


class Bill(StatesGroup):
    bill = State()


booking = Router()


@booking.callback_query(F.data.startswith("delete"))
async def begin_booking(callback: CallbackQuery) -> None:
    try:
        booking_id = callback.data.split("_")[-1]
        is_deleted = await db.delete_booking_by_id(booking_id=int(booking_id))
        if is_deleted is not True:
            await callback.answer("🚩 Ошибка при отмене бронирования!")
            return
        await callback.answer("✅ Бронирование отменено!")
        await callback.message.delete()
    except Exception as e:
        print(e)
        await show_error_callback(callback=callback)


@booking.callback_query(F.data.startswith("pay"))
async def process_payment(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
        booking_id = int(callback.data.split("_")[-1])
        booking_data = await db.get_booking_data_by_id(booking_id=booking_id)
        if booking_data is None:
            await show_error_callback(callback=callback)
            return
        text = await create_payment_text(amount=booking_data["amount"])
        reply_markup = await attach_bill_kb(booking_id=booking_id)
        await callback.message.edit_text(
            text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(e)
        await show_error_callback(callback=callback)


@booking.callback_query(F.data.startswith("bill"))
async def start_receiving_bill(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        # booking_id = int(callback.data.split("_")[-1])
        await callback.answer()
        print(PATH_TO_DOCUMENTS)
        # await callback.message.edit_text(
        #     text=BILL_ATTACH_TEXT,
        # )
        # await state.set_state(Bill.bill)
    except Exception as e:
        print(e)
        await show_error_callback(callback=callback)


@booking.message(Bill.bill, F.content_type.in_({"photo", "document"}))
async def get_bill(message: Message, state: FSMContext):
    try:
        destination = PATH_TO_DOCUMENTS

        # Проверка типа файла - документ
        if message.document is not None:
            # Получение названия файла
            file_name = message.document.file_name

            # Создание полного пути до документа
            destination += file_name

            # Скачивание документа
            await bot.download(file=message.document.file_id, destination=destination)
        elif message.photo is not None:
            # Скачивание файла до destination по имени unique_id
            await bot.download(
                file=message.photo[-1],
                destination=destination + message.photo[-1].file_unique_id + ".jpg",
            )
            file_name = message.photo[-1].file_unique_id + ".jpg"
    except Exception as e:
        print(e)
