async def create_booking_text(start_time: str, end_time: str, amount: str) -> str:
    return f"""
ℹ️ Информация о бронировании:

🕑 Дата и время заселения: {start_time}

🕛 Дата и время выезда: {end_time}

💸 Итого к оплате: {amount} ₽
"""


async def create_payment_text(text: str, amount: float) -> str:
    """
    Добавляет сумму к тексту из БД, сохраняя HTML-форматирование
    """
    formatted_amount = f"<b>{int(amount)}</b>"
    return f"{text}\nСумма к оплате: {formatted_amount} руб."

BILL_ATTACH_TEXT = "📝 Прикрепите 1 (один) файл или фотографию с чеком оплаты!"
