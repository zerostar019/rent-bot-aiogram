from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def start_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="⌚️ Забронировать", callback_data="booking")],
        [InlineKeyboardButton(text="ℹ️ Получить информацию", callback_data="info")],
        [InlineKeyboardButton(text="💬 Связаться с поддержкой", callback_data="help")],
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return keyboard


async def help_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📜 Правила", callback_data="rules"),
            InlineKeyboardButton(text="💸 Оплата", callback_data="_pay_rules"),
        ],
        [InlineKeyboardButton(text="📍 Местоположение", callback_data="location")],
        [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="menu")],
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return keyboard


async def return_to_help_menu() -> InlineKeyboardMarkup:
    button = [[InlineKeyboardButton(text="⬅️ Вернуться назад", callback_data="info")]]

    keyboard = InlineKeyboardMarkup(inline_keyboard=button)

    return keyboard


async def return_to_menu() -> InlineKeyboardMarkup:
    button = [[InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="menu")]]

    keyboard = InlineKeyboardMarkup(inline_keyboard=button)

    return keyboard
