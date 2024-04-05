from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime


async def create_timepicker(is_today: bool = False) -> InlineKeyboardMarkup:
    start = 0
    if is_today is True:
        start = datetime.now().hour
    builder = InlineKeyboardBuilder()
    for i in range(start, 24, 1):
        builder.add(
            InlineKeyboardButton(
                text=f'{i}.00-{ i+1 }.00', callback_data=f'time_{i}')
        )

    builder.adjust(3)
    builder.row(InlineKeyboardButton(
        text='⬅️ Назад', callback_data='pick_date'))
    return builder.as_markup()


async def edit_timepicker(data, is_today: bool = False) -> InlineKeyboardMarkup:
    start = 0
    if is_today is True:
        start = datetime.now().hour
    builder = InlineKeyboardBuilder()
    for i in range(start, 24, 1):
        if i in data:
            builder.add(
                InlineKeyboardButton(
                    text=f'✅ {i}.00-{ i+1 }.00', callback_data=f'time_{i}_activated')
            )
        else:
            builder.add(
                InlineKeyboardButton(
                    text=f'{i}.00-{ i+1 }.00', callback_data=f'time_{i}')
            )

    sum = len(data) * 1000
    builder.adjust(3)
    if len(data) > 2:
        times = '_'.join(str(element) for element in data)
        builder.row(InlineKeyboardButton(
            text=f'💸 К оплате {sum} руб.', callback_data=f'pay_{sum}_{times}'))
    builder.row(InlineKeyboardButton(
        text='⬅️ Назад', callback_data='pick_date'))

    return builder.as_markup()


async def approve_reservation() -> InlineKeyboardMarkup:
    button = [
        [InlineKeyboardButton(text='✅ Подтвердить', callback_data='approve')],
        [InlineKeyboardButton(text='🚫 Отменить', callback_data='pick_date')]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=button)

    return keyboard


async def help_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text='📜 Правила', callback_data='rules'),
         InlineKeyboardButton(text='💸 Оплата', callback_data='_pay_rules')],
         [InlineKeyboardButton(text='📍 Местоположение', callback_data='location')],
        [InlineKeyboardButton(text='⬅️ Вернуться в меню', callback_data='menu')]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return keyboard


async def return_to_help_menu() -> InlineKeyboardMarkup:
    button = [
        [InlineKeyboardButton(text='⬅️ Вернуться назад', callback_data='info')]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=button)

    return keyboard


async def return_to_menu() -> InlineKeyboardMarkup:
    button = [
        [InlineKeyboardButton(text='⬅️ Вернуться в меню', callback_data='menu')]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=button)

    return keyboard