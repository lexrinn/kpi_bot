# app/main.py — РАБОТАЕТ НА RENDER И ЛОКАЛЬНО. ТОЧКА.
import asyncio
import logging
import os

import aiohttp.web
import pytz
from aiogram import Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot import bot
from app.services.data_manager import DataManager
from app.config import UPDATE_TIMES, TIMEZONE
from app.handlers import start_router, kpi_router, monitoring_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()
dp.include_router(start_router)
dp.include_router(kpi_router)
dp.include_router(monitoring_router)

dm = DataManager()


async def update_cache_job():
    logger.info("Обновление кэша...")
    success = await asyncio.to_thread(dm.update_cache)
    logger.info("Кэш обновлён!" if success else "Ошибка кэша")


async def on_startup(app):
    await update_cache_job()
    if os.getenv("RENDER"):
        webhook_url = f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/webhook"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook установлен: {webhook_url}")


async def on_shutdown(app):
    await bot.delete_webhook()


def create_app() -> aiohttp.web.Application:
    app = aiohttp.web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Webhook роут
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")

    # Простой роут, чтобы Render видел живой сервис
    app.router.add_get("/", lambda r: aiohttp.web.Response(text="KPI Bot работает!"))

    # Планировщик
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
    for h, m in UPDATE_TIMES:
        scheduler.add_job(update_cache_job, "cron", hour=h, minute=m)
    scheduler.start()

    return app


# ─────── ОСНОВНОЙ ЗАПУСК ───────
if __name__ == "__main__":
    # Локально — polling
    if not os.getenv("RENDER"):
        logger.info("Запуск в режиме polling (локально)")
        asyncio.run(dp.start_polling(bot))
    else:
        # На Render — webhook
        app = create_app()
        port = int(os.getenv("PORT", 10000))
        logger.info(f"Запуск webhook на порту {port}")
        aiohttp.web.run_app(app, host="0.0.0.0", port=port)
