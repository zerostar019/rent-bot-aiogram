async def create_booking_text(start_time: str, end_time: str, amount: str) -> str:
    return f"""
ℹ️ Информация о бронировании:

🕑 Дата и время заселения: {start_time}

🕛 Дата и время выезда: {end_time}

💸 Итого к оплате: {amount} ₽
"""


async def create_payment_text(amount: str) -> str:
    return f"💸 Внесите оплату в течение 20 минут по указанным ниже реквизитам и нажмите кнопку «❇️ Прикрепить чек», чтобы отправить чек администратору для проверки!\n\nСумма к оплате: <b>{str(amount).split(".")[0]} руб.</b>\nБанк: <b>Cбер</b>\n\nНомер карты <i>(Нажмите, чтобы скопировать)</i>: <pre>4274278800022462</pre>\n\n"


BILL_ATTACH_TEXT = "📝 Прикрепите 1 (один) файл или фотографию с чеком оплаты!"