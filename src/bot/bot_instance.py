from aiogram import Bot
from config import env

bot = Bot(token=env.TOKEN.get_secret_value())
