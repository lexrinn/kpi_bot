# app/bot.py
import os
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ←←←←← ВОТ ФИКС: берём токен напрямую из окружения ←←←←←
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения!")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

def get_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мой KPI"), KeyboardButton(text="Мои недоработки")]
        ],
        resize_keyboard=True
    )
