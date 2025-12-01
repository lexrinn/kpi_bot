# app/main.py
import asyncio
import logging
import os

import pytz
from aiogram import Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot import bot
from app.services.data_manager import DataManager
from app.config import UPDATE_TIMES, TIMEZONE
from app.handlers import start_router, kpi_router, monitoring_router

# ─────────────────────── ЛОГИ ───────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────── ДИСПЕТЧЕР ───────────────────────
dp = Dispatcher()
dp.include_router(start_router)
dp.include_router(kpi_router)
dp.include_router(monitoring_router)

# ─────────────────────── МЕНЕДЖЕР ДАННЫХ ───────────────────────
dm = DataManager()


async def update_cache_job():
    """Обновление кэша из Google Sheets"""
    logger.info("Запуск планового обновления кэша...")
    success = await asyncio.to_thread(dm.update_cache)
    if success:
        logger.info("Кэш успешно обновлён")
    else:
        logger.error("Ошибка обновления кэша")


async def main():
    # ───── Планировщик обновлений (10:00 и 16:00 МСК) ─────
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
    for hour, minute in UPDATE_TIMES:
        scheduler.add_job(update_cache_job, "cron", hour=hour, minute=minute)
    scheduler.start()

    # ───── Первое обновление сразу при старте ─────
    await update_cache_job()

    # ───── Режим запуска: webhook на Render, polling везде остальном ─────
    if os.getenv("RENDER"):  # ← автоматически true только на Render
        service_name = os.getenv("RENDER_SERVICE_NAME")
        webhook_url = f"https://{service_name}.onrender.com/webhook"

        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook установлен: {webhook_url}")

        # На Render ничего больше не запускаем — aiohttp держит процесс живым
        await asyncio.Event().wait()  # держим процесс бесконечно

    else:
        # Локально и на PythonAnywhere — обычный polling
        logger.info("Запуск в режиме polling")
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
