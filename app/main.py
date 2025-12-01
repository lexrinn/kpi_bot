import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from aiogram import Dispatcher
from .bot import bot
from .services.data_manager import DataManager
from .config import UPDATE_TIMES, TIMEZONE
from .handlers import start_router, kpi_router, monitoring_router

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(kpi_router)
dp.include_router(monitoring_router)

dm = DataManager()

async def update_job():
    await asyncio.to_thread(dm.update_cache)

async def main():
    scheduler = AsyncIOScheduler()
    for h, m in UPDATE_TIMES:
        scheduler.add_job(update_job, "cron", hour=h, minute=m, timezone=pytz.timezone(TIMEZONE))
    scheduler.start()

    await update_job()  # сразу при старте
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())