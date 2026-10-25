from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramAPIError
from constants import ERROR_TEXT
from handlers.keyboard.kb import return_to_menu
import asyncio
import html
import logging
from typing import Any, Iterable, Optional


logger = logging.getLogger(__name__)


async def notify_admin_error(error: Exception, context: str = "") -> None:
    """Сохраняет техническую ошибку в журнале контейнера.

    Ошибки больше не отправляются в Telegram-чат: в чате должны быть
    только рабочие сообщения, а traceback остаётся для диагностики на сервере.
    """
    logger.error(
        "Ошибка в боте (context=%s): %s: %s",
        context or "unknown",
        type(error).__name__,
        error,
        exc_info=(type(error), error, error.__traceback__),
    )


async def delete_message_safely(message: Message) -> bool:
    """Удаляет сообщение, но не прерывает сценарий из-за ограничений Telegram."""
    try:
        await message.delete()
        return True
    except TelegramAPIError as error:
        logger.info(
            "Telegram не удалил сообщение chat_id=%s message_id=%s: %s",
            getattr(getattr(message, "chat", None), "id", "unknown"),
            getattr(message, "message_id", "unknown"),
            error,
        )
        return False


async def show_error_callback(callback: CallbackQuery) -> None:
    try:
        keyboard = await return_to_menu()
        await callback.message.edit_text(text=ERROR_TEXT, reply_markup=keyboard)
    except Exception:
        try:
            await callback.answer("⚠️ Произошла ошибка", show_alert=True)
        except Exception:
            pass


async def show_error_message(msg: Message, message: Message) -> None:
    try:
        keyboard = await return_to_menu()
        if msg:
            await msg.edit_text(text=ERROR_TEXT, reply_markup=keyboard)
        else:
            await message.answer(text=ERROR_TEXT, reply_markup=keyboard)
    except Exception:
        try:
            await message.answer("⚠️ Произошла ошибка")
        except Exception:
            pass


def escape_html(text: Optional[str]) -> str:
    """Экранирует пользовательский текст для parse_mode="HTML".

    Без этого любое сообщение с '<' или '&' роняет send_message
    с TelegramBadRequest, и админ его просто не получает.
    """
    if not text:
        return ""
    return html.escape(text, quote=False)


async def notify_admins(
    admins: Iterable[Any],
    text: str,
    reply_markup=None,
    parse_mode: str = "HTML",
) -> int:
    """Рассылает уведомление всем админам параллельно.

    Раньше рассылка шла последовательно с asyncio.sleep(1) на каждого админа,
    из-за чего обработчик входящего сообщения блокировался на N секунд
    и Telegram успевал повторить webhook. Теперь отправка идёт разом,
    а ошибка по одному админу не мешает остальным.
    """
    admin_ids = [int(admin) for admin in (admins or [])]
    if not admin_ids:
        return 0

    from bot.bot_instance import get_bot

    bot = get_bot()

    async def send(chat_id: int):
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )

    results = await asyncio.gather(
        *(send(chat_id) for chat_id in admin_ids), return_exceptions=True
    )

    delivered = 0
    for chat_id, result in zip(admin_ids, results):
        if isinstance(result, Exception):
            await notify_admin_error(result, f"notify_admins chat_id={chat_id}")
        else:
            delivered += 1
    return delivered
