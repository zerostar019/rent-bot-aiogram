# bot/bot_instance.py
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import ClientTimeout
from config import env
from typing import Optional

bot: Optional[Bot] = None

async def create_bot() -> Bot:
    """Асинхронно создает бота (с прокси, если задан PROXY)"""
    global bot
    
    if bot is not None:
        return bot

    # PROXY опционален: без него сессия создаётся как обычно.
    kwargs = dict(timeout=ClientTimeout(total=60, connect=20, sock_read=30))
    if env.PROXY:
        kwargs["proxy"] = env.PROXY

    session = AiohttpSession(**kwargs)

    bot = Bot(token=env.TOKEN.get_secret_value(), session=session)
    return bot

def get_bot() -> Bot:
    if bot is None:
        raise RuntimeError("Bot not initialized. Call create_bot() first.")
    return bot

# Для обратной совместимости
def __getattr__(name: str):
    if name == "bot":
        return get_bot()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
