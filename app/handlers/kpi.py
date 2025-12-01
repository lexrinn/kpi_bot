# app/handlers/kpi.py
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from app.services.data_manager import DataManager
from app.utils import get_kpi_indicator, get_emoji, get_sticker
from app.bot import get_keyboard

router = Router()
dm = DataManager()

@router.message(F.text == "Мой KPI")
async def my_kpi(message: Message):
    username = message.from_user.username
    if not username:
        return await message.answer("Установи @username")

    row = await asyncio.to_thread(dm.get_user_data, "kpi", username)
    if not row or len(row) < 5:
        return await message.answer("Твои KPI не найдены")

    cr_val, qa_val = row[3], row[4]
    cr_emo = get_emoji(get_kpi_indicator(cr_val, "CR"))
    qa_emo = get_emoji(get_kpi_indicator(qa_val, "QA"))

    # Худший показатель → стикер
    priority = {"Red":1, "Yellow":2, "Green":3, "Blue":4, "Purple":5}
    worst = cr_emo if priority.get(get_kpi_indicator(cr_val, "CR"), 6) <= priority.get(get_kpi_indicator(qa_val, "QA"), 6) else qa_emo

    sticker = get_sticker(worst, "KPI")
    if sticker:
        try:
            await message.answer_sticker(sticker)
        except:
            pass

    text = f"**KPI:**\n\n{cr_emo} CR: **{cr_val}**\n{qa_emo} QA: **{qa_val}**"
    await message.answer(text, parse_mode="Markdown", reply_markup=get_keyboard())