from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardButton,
    WebAppInfo,
    InlineKeyboardMarkup,
)
from handlers.keyboard.kb import help_menu, return_to_menu, return_to_help_menu
from bot.ws import manager
from database.psql_db import db
from bot.bot_instance import get_bot
from utils import escape_html, notify_admin_error, notify_admins
from constants import (
    APARTMENT_ADDRESS,
    SUPPORT_TEXT,
    RULES_TEXT,
    REQUISITES_TEXT,
    SHOW_INFO_TEXT,
)
import asyncio
import pathlib

PATH_TO_DOCUMENTS = str(pathlib.Path(__file__).resolve().parent.parent) + "/documents/"


def safe_filename(filename: str) -> str:
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    return "".join(c for c in filename if c in keep) or "file"


support = Router()

chat_button = [
    [
        InlineKeyboardButton(
            text="💬 Чаты",
            web_app=WebAppInfo(
                url="https://businesspochta.kazan.hlab.kz/admin/admin/dashboard/chat"
            ),
        )
    ],
]

chat_keyboard = InlineKeyboardMarkup(inline_keyboard=chat_button)


@support.callback_query(F.data == "info")
async def show_info(callback: CallbackQuery):
    keyboard = await help_menu()
    await callback.message.edit_text(SHOW_INFO_TEXT, reply_markup=keyboard)


@support.callback_query(F.data == "rules")
async def show_rules(callback: CallbackQuery):
    keyboard = await return_to_help_menu()
    await callback.message.edit_text(text=RULES_TEXT, reply_markup=keyboard)


@support.callback_query(F.data == "_pay_rules")
async def show_pay_rules(callback: CallbackQuery):
    keyboard = await return_to_help_menu()
    await callback.message.edit_text(text=REQUISITES_TEXT, reply_markup=keyboard)


@support.callback_query(F.data == "location")
async def show_location(callback: CallbackQuery):
    keyboard = await return_to_help_menu()
    await callback.message.edit_text(text=APARTMENT_ADDRESS, reply_markup=keyboard)


@support.callback_query(F.data == "help")
async def call_manager(callback: CallbackQuery):
    keyboard = await return_to_menu()
    await callback.message.edit_text(text=SUPPORT_TEXT, reply_markup=keyboard)


@support.message(F.content_type.in_({"text"}))
async def process_chatting_with_admin(message: Message):
    try:
        user_text = message.text.strip()
        msg = await db.save_message_from_bot(
            message_text=user_text, user_id=message.chat.id
        )
        admins = await db.get_admins()
        notify_text = (
            f"Новое сообщение от {message.chat.id}: \n\n{escape_html(user_text)}"
        )
        # Рассылка админам и обновление панели идут параллельно:
        # обработчик webhook больше не ждёт по секунде на каждого админа.
        await asyncio.gather(
            notify_admins(admins, notify_text, reply_markup=chat_keyboard),
            manager.broadcast(data=msg),
        )
    except Exception as e:
        await notify_admin_error(e, "process_chatting_with_admin")


@support.message(F.content_type.in_({"document", "photo"}))
async def get_photo_or_document(message: Message):
    try:
        message_text = ""
        if message.caption is not None:
            message_text = message.caption
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
        saved = await db.save_file_from_bot(
            file_name=file_name,
            file_path=file_path,
            user_id=message.chat.id,
            chat_id=message.chat.id,
            message_text=message_text,
        )
        admins = await db.get_admins()
        notify_text = f"Новое сообщение от {message.chat.id}"
        if message_text:
            notify_text += f":\n\n{escape_html(message_text)}"
        await asyncio.gather(
            notify_admins(admins, notify_text, reply_markup=chat_keyboard),
            manager.broadcast(data=saved),
        )
    except Exception as e:
        await notify_admin_error(e, "get_photo_or_document")
