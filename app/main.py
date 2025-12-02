# main.py — 100 % обновляет кэш при старте
import asyncio
import logging
import os
import aiohttp.web
from aiogram import Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

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

# ←←←←← ВОТ ЭТО ГЛАВНОЕ ←←←←←
dm = DataManager()  # создаём экземпляр один раз


async def update_cache_job():
    logger.info("Запуск обновления кэша...")
    success = await asyncio.to_thread(dm.update_cache)  # ← используем один и тот же dm
    if success:
        logger.info("КЭШ УСПЕШНО ОБНОВЛЁН")
    else:
        logger.error("ОШИБКА ОБНОВЛЕНИЯ КЭША")


async def on_startup(app):
    await update_cache_job()  # ← ПЕРВОЕ ОБНОВЛЕНИЕ СРАЗУ ПРИ СТАРТЕ

    if os.getenv("RENDER"):
        webhook_url = f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com/webhook"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook установлен: {webhook_url}")


async def on_shutdown(app):
    await bot.delete_webhook()


def create_app():
    app = aiohttp.web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    app.router.add_post("/webhook", handler.handle)

    app.router.add_get("/", lambda r: aiohttp.web.Response(text="KPI Bot работает!"))
    app.router.add_get("/ping", lambda r: aiohttp.web.Response(text="OK"))

    # Планировщик 10:00 и 16:00
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
    for h, m in UPDATE_TIMES:
        scheduler.add_job(update_cache_job, "cron", hour=h, minute=m)
    scheduler.start()

    return app


if __name__ == "__main__":
    if os.getenv("RENDER"):
        app = create_app()
        port = int(os.getenv("PORT", 10000))
        logger.info(f"Запуск webhook на порту {port}")
        aiohttp.web.run_app(app, host="0.0.0.0", port=port)
    else:
        logger.info("Запуск локально — polling")
        # ←←←←← И ЗДЕСЬ ТОЖЕ ОБНОВЛЯЕМ КЭШ ПРИ СТАРТЕ ←←←←←
        asyncio.run(asyncio.to_thread(dm.update_cache))
        asyncio.run(dp.start_polling(bot))
