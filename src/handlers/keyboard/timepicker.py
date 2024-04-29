from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from datetime import datetime


async def create_timepicker(rented_times: List[dict] = [], is_today: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    MIN_RENT_HOURS = 3
    today_max_range = []      

    not_available_hours = []
    for rented_time in rented_times:
        start_time = rented_time.get('rent_start')
        end_time = rented_time.get('rent_end')
        for hour in range(start_time, end_time + 1):  # Включаем конечный час в занятые
            not_available_hours.append(hour)

    # Сортировка списка занятых часов
    not_available_hours = sorted(not_available_hours)

    is_not_enough = False
    start = 0
    if is_today:
        is_not_enough = set(today_max_range).issubset(not_available_hours)
        start = datetime.now().hour + 1
        today_max_range = [h for h in range(start, 24)]


    if len(not_available_hours) == 0:  # Если занятых часов нет
        for hour in range(start, 24):
            builder.add(InlineKeyboardButton(
                text=f'{hour}.00', callback_data=f'hour_{hour}'))
        builder.adjust(3)
        builder.row(InlineKeyboardButton(
            text='⬅️ Назад', callback_data='pick_date'))
        if start == 24:
            return (builder.as_markup(), 0)
        else:
            return (builder.as_markup(), 1)
    elif len(not_available_hours) == 23 or len(not_available_hours) == 24 or (is_today and is_not_enough):  # Если все часы заняты
        builder.row(InlineKeyboardButton(
            text='⬅️ Назад', callback_data='pick_date'))
        return (builder.as_markup(), 0)
    else:  # Иначе выводим доступные интервалы
        if is_today and start > 0:
            last_available_hour = start
        else:
            last_available_hour = -1
        for hour in not_available_hours:
            if hour - last_available_hour >= MIN_RENT_HOURS + 1:  # + 1 для учёта часа уборки
                for available_hour in range(last_available_hour + 1, hour):
                    if available_hour >= start and available_hour + MIN_RENT_HOURS <= 24:
                        builder.add(InlineKeyboardButton(
                            text=f'{available_hour}.00', callback_data=f'hour_{available_hour}'))
            last_available_hour = hour  # Обновляем последний доступный час

        # Проверяем интервал после последнего занятого часа с учётом часа уборки
        if not_available_hours:
            last_rented_hour = not_available_hours[-1]
            if 24 - (last_rented_hour + 1) >= MIN_RENT_HOURS:
                for available_hour in range(last_rented_hour + 1, 24):
                    builder.add(InlineKeyboardButton(
                        text=f'{available_hour}.00', callback_data=f'hour_{available_hour}'))

        builder.adjust(3)
        builder.row(InlineKeyboardButton(
            text='⬅️ Назад', callback_data='pick_date'))
        return (builder.as_markup(), 1)


async def edit_timepicker(rented_times: List[dict], start_hour: int | None, end_hour: int | None, is_today: bool = False):
    builder = InlineKeyboardBuilder()

    MIN_RENT_HOURS = 3

    start = datetime.now().hour + 1 if is_today else 0

    not_available_hours = []
    for rented_time in rented_times:
        start_time = rented_time.get('rent_start')
        end_time = rented_time.get('rent_end')
        for hour in range(start_time, end_time + 1):
            not_available_hours.append(hour)

    rent_time = []
    if start_hour is not None:
        if end_hour is not None:
            for i in range(start_hour, end_hour + 1):
                rent_time.append(i)
        else:
            rent_time = [start_hour]

    total_price = 0
    if len(rent_time) == 2:
        total_price = 8000
    elif len(rent_time) == 3:
        total_price = 10000
    elif len(rent_time) == 5:
        total_price = 13000
    elif len(rent_time) == 6:
        total_price = 15000
    elif len(rent_time) == 24:
        total_price = 25000
    else:
        total_price = len(rent_time) * 4000


    if not not_available_hours:
        for hour in range(start, 24):
            if hour in rent_time:
                builder.add(InlineKeyboardButton(
                    text=f'✅ {hour}.00', callback_data=f'hour_{hour}'))
            else:
                builder.add(InlineKeyboardButton(
                    text=f'{hour}.00', callback_data=f'hour_{hour}'))
        builder.adjust(3)
    else:
        available_hours = [h for h in range(start, 24) if h not in not_available_hours]
        for hour in available_hours:
            if hour in rent_time:  # Если час уже выбран для аренды
                builder.add(InlineKeyboardButton(
            text=f'✅ {hour}.00', callback_data=f'hour_{hour}'))
            else:
                builder.add(InlineKeyboardButton(
            text=f'{hour}.00', callback_data=f'hour_{hour}'))
        builder.adjust(3)

    if len(rent_time) >= MIN_RENT_HOURS:
        builder.row(InlineKeyboardButton(
            text=f'💸 К оплате {total_price} руб.', callback_data=f'pay_{total_price}'))
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
        [InlineKeyboardButton(text='📍 Местоположение',
                              callback_data='location')],
        [InlineKeyboardButton(text='⬅️ Вернуться в меню',
                              callback_data='menu')]
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
        [InlineKeyboardButton(text='⬅️ Вернуться в меню',
                              callback_data='menu')]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=button)

    return keyboard
