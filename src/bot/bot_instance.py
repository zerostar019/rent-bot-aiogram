from aiogram import Bot
from src.config import env

bot = Bot(token=env.TOKEN.get_secret_value())