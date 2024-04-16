from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from datetime import datetime


async def create_timepicker(rented_times: List[dict] = [], is_today: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    MIN_RENT_HOURS = 3
    AVAILABLE_HOURS = list(range(0, 24))

    if is_today:
        start = datetime.now().hour + 1
    else:
        start = 0

    not_available_hours = []
    for rented_time in rented_times:
        start_time = rented_time.get('rent_start')
        end_time = rented_time.get('rent_end')
        for hour in range(start_time, end_time):
            not_available_hours.append(hour)
            if hour in AVAILABLE_HOURS:
                AVAILABLE_HOURS.remove(hour)
        
    if not not_available_hours:  # Если занятых часов нет
        for hour in range(start, 24):
            builder.add(InlineKeyboardButton(text=f'{hour}.00', callback_data=f'hour_{hour}'))
        builder.adjust(3)
        builder.row(InlineKeyboardButton(
        text='⬅️ Назад', callback_data='pick_date'))
        return (builder.as_markup(), 1)
    elif len(not_available_hours) == 23 or len(not_available_hours) == 24:  # Если все часы заняты
        builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='pick_date'))
        return (builder.as_markup(), 0)
    else:  # Иначе выводим доступные интервалы
        for i in range(len(not_available_hours) - 1):
            if not_available_hours[i] + 1 != not_available_hours[i + 1]:
                for hour in range(not_available_hours[i] + 1, not_available_hours[i + 1]):
                    if hour >= start and hour + MIN_RENT_HOURS <= 24:
                        builder.add(InlineKeyboardButton(text=f'{hour}.00', callback_data=f'hour_{hour}'))
        builder.adjust(3)
        builder.row(InlineKeyboardButton(
        text='⬅️ Назад', callback_data='pick_date'))
    
        return (builder.as_markup(), 1)


async def edit_timepicker(rented_times: List[dict], start_hour: int | None, end_hour: int | None, is_today: bool = False):
    builder = InlineKeyboardBuilder()
    
    MIN_RENT_HOURS = 3
    AVAILABLE_HOURS = list(range(0, 24))

    if is_today:
        start = datetime.now().hour + 1
    else:
        start = 0

    not_available_hours = []
    for rented_time in rented_times:
        start_time = rented_time.get('rent_start')
        end_time = rented_time.get('rent_end')
        for hour in range(start_time, end_time):
            not_available_hours.append(hour)
            if hour in AVAILABLE_HOURS:
                AVAILABLE_HOURS.remove(hour)

    rent_time = []
    if start_hour is not None:
        if end_hour is not None:
            for i in range(start_hour, end_hour + 1):
                rent_time.append(i)
        else:
            rent_time = [start_hour]

    total_price = len(rent_time) * 1000
        
    if not not_available_hours:  
        for hour in range(start, 24):
            if hour in rent_time:
                builder.add(InlineKeyboardButton(text=f'✅ {hour}.00', callback_data=f'hour_{hour}'))
            else:
                builder.add(InlineKeyboardButton(text=f'{hour}.00', callback_data=f'hour_{hour}'))
        builder.adjust(3)
        if len(rent_time) >= MIN_RENT_HOURS:
            builder.row(InlineKeyboardButton(text=f'💸 К оплате {total_price} руб.', callback_data=f'pay_{total_price}'))
        builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='pick_date'))
    elif len(not_available_hours) == 24:  
        builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='pick_date'))
    else:  
        for i in range(len(not_available_hours) - 1):
            if not_available_hours[i] + 1 != not_available_hours[i + 1]:
                for hour in range(not_available_hours[i] + 1, not_available_hours[i + 1]):
                    if hour >= start and hour + MIN_RENT_HOURS <= 24:
                        if hour in rent_time:
                            builder.add(InlineKeyboardButton(text=f'✅ {hour}.00', callback_data=f'hour_{hour}'))
                        else:
                            builder.add(InlineKeyboardButton(text=f'{hour}.00', callback_data=f'hour_{hour}'))
        builder.adjust(3)
        if len(rent_time) >= MIN_RENT_HOURS:
            builder.row(InlineKeyboardButton(text=f'💸 К оплате {total_price} руб.', callback_data=f'pay_{total_price}'))
        builder.row(InlineKeyboardButton(text='⬅️ Назад', callback_data='pick_date'))

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