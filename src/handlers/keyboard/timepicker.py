from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from datetime import datetime


async def create_timepicker(rented_times: List[dict] = [], is_today: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    MIN_RENT_HOURS = 3
    AVAILABLE_HOURS = list(range(0, 24))
    NOT_AVAILABLE_HOURS = []

    if is_today is True:
        start = datetime.now().hour + 1
    else:
        start = 0

    for rented_time in rented_times:
        start_time = rented_time.get('rent_start')
        end_time = rented_time.get('rent_end')
        for hour in range(start_time, end_time):
            if hour in AVAILABLE_HOURS:
                NOT_AVAILABLE_HOURS.append(hour)
                AVAILABLE_HOURS.remove(hour)
        
    for hour in range(start, 24):
        if hour in AVAILABLE_HOURS and hour + MIN_RENT_HOURS <= 24 and hour + MIN_RENT_HOURS not in NOT_AVAILABLE_HOURS:
            builder.add(
                InlineKeyboardButton(text=f'{hour}.00', callback_data=f'hour_{hour}')
            )

    builder.adjust(3)
    builder.row(InlineKeyboardButton(
        text='⬅️ Назад', callback_data='pick_date'))
    return builder.as_markup()


async def edit_timepicker(rented_times: List[dict], start_hour: int | None, end_hour: int | None, is_today: bool = False):
    builder = InlineKeyboardBuilder()
    
    MIN_RENT_HOURS = 3
    AVAILABLE_HOURS = list(range(0, 24))
    NOT_AVAILABLE_HOURS = []

    if is_today is True:
        start = datetime.now().hour + 1
    else:
        start = 0

    for rented_time in rented_times:
        start_time = rented_time.get('rent_start')
        end_time = rented_time.get('rent_end')
        for hour in range(start_time, end_time):
            if hour in AVAILABLE_HOURS:
                NOT_AVAILABLE_HOURS.append(hour)
                AVAILABLE_HOURS.remove(hour)


    if end_hour is not None:
        choosen_range = list(range(start_hour, end_hour + 1))
    elif start_hour is None:
        choosen_range = []
    else:
        choosen_range = [start_hour]
        
    for hour in range(start, 24):
        if hour in AVAILABLE_HOURS and hour + MIN_RENT_HOURS <= 24 and hour + MIN_RENT_HOURS not in NOT_AVAILABLE_HOURS:
            if hour in choosen_range:
                builder.add(
                    InlineKeyboardButton(text=f'✅ {hour}.00', callback_data=f'hour_{hour}')
            )
            else:
                builder.add(
                    InlineKeyboardButton(text=f'{hour}.00', callback_data=f'hour_{hour}')
                )

    for_pay = len(choosen_range) * 1000

    builder.adjust(3)
    if len(choosen_range) >= 2:
        builder.row(
            InlineKeyboardButton(
                text=f'К оплате {for_pay} руб.',
                callback_data=f'pay_{for_pay}'
            )
        )
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