from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from handlers.keyboard.kb import help_menu, return_to_menu, return_to_help_menu
from bot.ws import manager
from database.psql_db import db
from bot.bot_instance import bot
from constants import (
    APARTMENT_ADDRESS,
    SUPPORT_TEXT,
    RULES_TEXT,
    REQUISITES_TEXT,
    SHOW_INFO_TEXT,
)
import pathlib

PATH_TO_DOCUMENTS = str(pathlib.Path(__file__).resolve().parent.parent) + "/documents/"

support = Router()

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
        message = await db.save_message_from_bot(
            message_text=message.text.strip(), user_id=message.chat.id
        )
        await manager.broadcast(data=message)
    except Exception as e:
        print(e)


@support.message(F.content_type.in_({"document", "photo", "text"}))
async def get_photo_or_document(message: Message):
    try:
        message_text = ""
        if message.caption is not None:
            message_text = message.caption
        destination = PATH_TO_DOCUMENTS
        # Проверка типа файла - документ
        file_name = ""
        file_path = ""
        if message.document is not None:
            # Получение названия файла
            file_name = message.document.file_name
            # Создание полного пути до документа
            destination += file_name
            file_path = destination
            # Скачивание документа
            await bot.download(file=message.document.file_id, destination=destination)
        elif message.photo is not None:
            # Скачивание файла до destination по имени unique_id
            file_name = message.photo.pop().file_unique_id + ".jpg"
            destination += file_name
            file_path = destination
            await bot.download(
                file=message.photo[-1],
                destination=destination,
            )
        message = await db.save_file_from_bot(
            file_name=file_name,
            file_path=file_path,
            user_id=message.chat.id,
            chat_id=message.chat.id,
            message_text=message_text,
        )
        await manager.broadcast(data=message)
    except Exception as e:
        print(e)
