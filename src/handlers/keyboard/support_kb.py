from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def create_support_button(user_id: int) -> InlineKeyboardMarkup:
    button = [
        [InlineKeyboardButton(text='Ответить', callback_data=f'user_{user_id}')]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=button)

    return keyboard


async def cancel_enter() -> InlineKeyboardMarkup:
    button = [
        [InlineKeyboardButton(text='Отмена', callback_data='deny_answer')]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=button)

    return keyboard


async def approve_payment(user_id: int) -> InlineKeyboardMarkup:
    button = [
        [InlineKeyboardButton(text='Подтвердить оплату', callback_data=f'approvePay_{user_id}')],
        [InlineKeyboardButton(text='Написать сообщение', callback_data=f'answerBook_{user_id}')]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=button)

    return keyboard