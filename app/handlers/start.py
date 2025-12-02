from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from ..bot import get_keyboard

router = Router()

@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Выбери пункт:", reply_markup=get_keyboard())

@router.message(Command("update"))
async def upd(message: Message):
    from ..services.data_manager import DataManager
    ok = DataManager().update_cache()
    await message.answer("Готово!" if ok else "Ошибка")
