# app/handlers/monitoring.py
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from app.services.data_manager import DataManager
from app.utils import get_bugs_indicator, get_emoji, get_sticker
from app.bot import get_keyboard

router = Router()
dm = DataManager()

@router.message(F.text == "Мои недоработки")
async def my_bugs(message: Message):
    username = message.from_user.username
    if not username:
        return await message.answer("Установи @username")

    row = await asyncio.to_thread(dm.get_user_data, "monitoring", username)
    if not row or len(row) < 5:
        return await message.answer("Данные по недоработкам не найдены")

    time_val = row[4]
    emo = get_emoji(get_bugs_indicator(time_val))

    sticker = get_sticker(get_bugs_indicator(time_val), "BUGS")
    if sticker:
        try:
            await message.answer_sticker(sticker)
        except:
            pass

    text = f"**Недоработки:**\n\n{emo} Время: **{time_val}**"
    await message.answer(text, parse_mode="Markdown", reply_markup=get_keyboard())