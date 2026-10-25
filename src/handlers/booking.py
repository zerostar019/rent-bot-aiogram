from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from utils import delete_message_safely, show_error_callback, notify_admin_error
from database.psql_db import db
from handlers.keyboard.kb import attach_bill_kb
from text import create_payment_text, BILL_ATTACH_TEXT
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import pathlib
from bot.bot_instance import get_bot
from bot.ws import manager
from datetime import datetime
from scheduler import scheduler
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def safe_filename(filename: str) -> str:
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    return "".join(c for c in filename if c in keep) or "file"


PATH_TO_DOCUMENTS = str(pathlib.Path(__file__).resolve().parent.parent) + "/documents/"


class Bill(StatesGroup):
    bill = State()
    booking_id = State()
    last_message = State()


booking = Router()


@booking.callback_query(F.data.startswith("delete"))
async def begin_booking(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await state.clear()
        if scheduler.get_job(f"{callback.message.chat.id}_job"):
            scheduler.remove_job(f"{callback.message.chat.id}_job")
        booking_id = callback.data.split("_")[-1]
        is_deleted = await db.delete_booking_by_id(booking_id=int(booking_id))
        if is_deleted is not True:
            await callback.answer("🚩 Ошибка при отмене бронирования!")
            return
        await callback.answer("✅ Бронирование отменено!")
        await delete_message_safely(callback.message)
    except Exception as e:
        await notify_admin_error(e, "begin_booking delete")
        await show_error_callback(callback=callback)


@booking.callback_query(F.data.startswith("pay"))
async def process_payment(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.answer()
        booking_id = int(callback.data.split("_")[-1])
        await state.update_data(booking_id=booking_id)
        booking_data = await db.get_booking_data_by_id(booking_id=booking_id)
        if booking_data is None:
            await show_error_callback(callback=callback)
            return
        payment_text = await db.get_field_text(field_name="payment_text")
        payment_text = str(payment_text).replace("\\n", "\n")
        text = await create_payment_text(
            text=payment_text, amount=booking_data["amount"]
        )
        reply_markup = await attach_bill_kb(booking_id=booking_id)
        await callback.message.edit_text(
            text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await notify_admin_error(e, "process_payment")
        await show_error_callback(callback=callback)


@booking.callback_query(F.data.startswith("bill"))
async def start_receiving_bill(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        data = await state.get_data()
        await callback.answer()
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❗️ Отменить бронь",
                        callback_data=f"delete_{data['booking_id']}",
                    )
                ]
            ]
        )
        msg = await callback.message.edit_text(
            text=BILL_ATTACH_TEXT, reply_markup=reply_markup
        )
        await state.update_data(
            last_message={"chat_id": msg.chat.id, "message_id": msg.message_id}
        )
        await state.set_state(Bill.bill)
    except Exception as e:
        scheduler.remove_job(f"{callback.message.chat.id}_job")
        await notify_admin_error(e, "start_receiving_bill")
        await show_error_callback(callback=callback)


@booking.message(Bill.bill, F.content_type.in_({"photo", "document"}))
async def get_bill(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        await get_bot().edit_message_reply_markup(
            chat_id=data["last_message"]["chat_id"],
            message_id=data["last_message"]["message_id"],
            reply_markup=None,
        )
        booking_data = await db.get_booking_data_by_id(booking_id=data["booking_id"])
        start_time = datetime.strptime(
            booking_data["time_interval"]["start"], "%Y-%m-%dT%H:%M:%S"
        ).strftime("%d.%m.%Y %H:%M")
        end_time = datetime.strptime(
            booking_data["time_interval"]["end"], "%Y-%m-%dT%H:%M:%S"
        ).strftime("%d.%m.%Y %H:%M")
        amount = booking_data["amount"]
        user_id = booking_data["id_user"]
        rent_type = "Посуточно"
        if booking_data["rent_type"] != "daily":
            rent_type = "Почасово"
        message_text = "👤 Пользователь отправил чек на оплату:\n\n"
        message_text += f"ℹ️ Период бронирования: {start_time} - {end_time}\n\n"
        message_text += f"💸 Сумма: {amount} ₽\n\n"
        message_text += f"📍 ID пользователя: {user_id}\n\n"
        message_text += f"🔑 Тип бронирования: {rent_type}\n\n"
        file_name = ""
        file_path = ""
        if message.document is not None:
            file_name = safe_filename(message.document.file_name or "document")
            file_path = PATH_TO_DOCUMENTS + file_name
            await get_bot().download(file=message.document.file_id, destination=file_path)
        elif message.photo is not None:
            file_name = safe_filename(message.photo[-1].file_unique_id + ".jpg")
            file_path = PATH_TO_DOCUMENTS + file_name
            await get_bot().download(
                file=message.photo[-1],
                destination=file_path,
            )
        msg = await db.save_file_from_bot(
            file_name=file_name,
            file_path=file_path,
            user_id=message.chat.id,
            chat_id=message.chat.id,
            message_text=message_text,
            booking_id=data["booking_id"],
        )
        await message.answer(
            "✅ 🎉 Подтверждение успешно прикреплено! Ожидайте обработку бронирования оператором. Оператор ответит в ближайшее время и подтвердит бронь!"
        )
        scheduler.remove_job(f"{message.chat.id}_job")
        await manager.broadcast(data=msg)
        admins = await db.get_admins()
        for admin in admins:
            await get_bot().send_message(
                chat_id=admin,
                text=f"ℹ️ Новое бронирование, проверьте чат с пользователем {message.chat.id}",
            )
        await state.clear()
    except Exception as e:
        await notify_admin_error(e, "get_bill")
