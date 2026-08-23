"""Кэш занятых дат в Redis.

Календарь бронирования дёргает /app/get-busy на каждое переключение дня,
а каждый такой запрос разворачивает generate_series на 60 дней вперёд.
Ответ кэшируется на короткий TTL и сбрасывается версией: любая запись
в rental увеличивает счётчик, из-за чего все старые ключи перестают
совпадать и читаются заново. Это исключает отдачу устаревшей занятости.
"""

import json
import logging

from bot.redis_instance import redis

_VERSION_KEY = "booking:busy:version"
_TTL_SECONDS = 120

logger = logging.getLogger(__name__)


async def _version() -> str:
    try:
        value = await redis.get(_VERSION_KEY)
        if value is None:
            await redis.set(_VERSION_KEY, 1)
            return "1"
        return str(value)
    except Exception as e:
        logger.warning("busy cache: не удалось прочитать версию: %s", e)
        return "0"


async def get_busy(scope: str, key: str):
    """Возвращает закэшированный ответ либо None."""
    try:
        version = await _version()
        raw = await redis.get(f"busy:{version}:{scope}:{key}")
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning("busy cache: чтение не удалось: %s", e)
        return None


async def set_busy(scope: str, key: str, value) -> None:
    try:
        version = await _version()
        await redis.set(
            f"busy:{version}:{scope}:{key}",
            json.dumps(value, default=str),
            ex=_TTL_SECONDS,
        )
    except Exception as e:
        logger.warning("busy cache: запись не удалась: %s", e)


async def invalidate() -> None:
    """Сбрасывает кэш после любого изменения броней."""
    try:
        await redis.incr(_VERSION_KEY)
    except Exception as e:
        logger.warning("busy cache: сброс не удался: %s", e)
