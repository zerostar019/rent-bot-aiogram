from aiogram import F, Router
from aiogram.types import CallbackQuery
from handlers.keyboard.kb import help_menu, return_to_menu, return_to_help_menu
from constants import (
    APARTMENT_ADDRESS,
    SUPPORT_TEXT,
    RULES_TEXT,
    REQUISITES_TEXT,
    SHOW_INFO_TEXT,
)

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
