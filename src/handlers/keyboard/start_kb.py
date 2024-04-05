from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def start_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text='📝 Записаться', callback_data='sign')],
        [InlineKeyboardButton(text='ℹ️ Получить информацию',
                              callback_data='info')],
        [InlineKeyboardButton(
            text='🗣 Связаться с поддержкой', callback_data='help')]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return keyboard
