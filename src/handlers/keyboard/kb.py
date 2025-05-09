from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


async def start_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="⌚️ Забронировать",
                web_app=WebAppInfo(url="https://ls06mn-91-142-83-218.ru.tuna.am/"),
            )
        ],
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


async def create_finish_booking_kb(booking_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Перейти к оплате", callback_data=f"pay_{booking_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🟥 Отменить бронирование", callback_data=f"delete_{booking_id}"
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def attach_bill_kb(booking_id: int) -> InlineKeyboardMarkup:
    button = [
        [
            InlineKeyboardButton(
                text="❇️ Прикрепить чек", callback_data=f"bill_{booking_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🟥 Отменить бронирование", callback_data=f"delete_{booking_id}"
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=button)
