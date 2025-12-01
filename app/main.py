# app/main.py
import asyncio
import logging
import os
from pathlib import Path

import aiohttp
import pytz
from aiogram import Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
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

async def on_startup(app):
    """Стартап: обновление кэша + webhook"""
    await update_cache_job()  # Первое обновление сразу

    if os.getenv("RENDER"):  # Только на Render
        webhook_url = f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/webhook"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook установлен: {webhook_url}")

async def on_shutdown(app):
    """Шатдаун: удаляем webhook"""
    await bot.delete_webhook()

async def main():
    # ───── Планировщик обновлений (10:00 и 16:00 МСК) ─────
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
    for hour, minute in UPDATE_TIMES:
        scheduler.add_job(update_cache_job, "cron", hour=hour, minute=minute)
    scheduler.start()

    # ───── Режим запуска ─────
    if os.getenv("RENDER"):
        # ───── WEBHOOK НА RENDER ─────
        app = aiohttp.web.Application()
        app.on_startup.append(on_startup)
        app.on_shutdown.append(on_shutdown)

        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")

        # Биндим порт для Render (0.0.0.0:PORT)
        port = int(os.getenv("PORT", 10000))
        host = "0.0.0.0"
        logger.info(f"Запуск webhook-сервера на {host}:{port}")
        aiohttp.web.run_app(app, host=host, port=port)

    else:
        # ───── POLLING ВЕЗДЕ ОСТАЛЬНОМ ─────
        logger.info("Запуск в режиме polling (локально)")
        await on_startup(None)  # Обновляем кэш
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
