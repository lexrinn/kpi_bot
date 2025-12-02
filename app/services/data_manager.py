# app/services/data_manager.py
import os
import json
import logging
from datetime import datetime
import asyncio

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


class DataManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cache = {"kpi": [], "monitoring": []}
            cls._instance.last_update = None
            cls._instance.client = None
        return cls._instance

    def _authenticate(self):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # 1. Из переменной окружения (для Render, Docker и т.п.)
        creds_json_str = os.getenv('GOOGLE_CREDS_JSON')
        if creds_json_str:
            try:
                creds_info = json.loads(creds_json_str)
                creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
                return gspread.authorize(creds)
            except Exception as e:
                logger.error(f"Ошибка парсинга GOOGLE_CREDS_JSON: {e}")

        # 2. Локальный файл creds.json (для разработки)
        key_file = os.getenv('GOOGLE_KEY_FILE', 'creds.json')
        if os.path.exists(key_file):
            try:
                creds = Credentials.from_service_account_file(key_file, scopes=scopes)
                return gspread.authorize(creds)
            except Exception as e:
                logger.error(f"Ошибка чтения {key_file}: {e}")

        logger.error("Не удалось авторизоваться в Google Sheets")
        return None

    async def update_cache(self) -> bool:
        """Обновляет кэш из Google Sheets. Возвращает True если всё ок."""
        sheet_name = os.getenv('GOOGLE_SHEET_NAME')
        if not sheet_name:
            logger.error("Не задан GOOGLE_SHEET_NAME в .env")
            return False

        if not self.client:
            self.client = await asyncio.to_thread(self._authenticate)
            if not self.client:
                return False

        try:
            spreadsheet = await asyncio.to_thread(self.client.open, sheet_name)
            logger.info(f"Открыта таблица: {spreadsheet.title}")

            kpi_ws = await asyncio.to_thread(spreadsheet.worksheet, 'kpi')
            mon_ws = await asyncio.to_thread(spreadsheet.worksheet, 'monitoring')

            kpi_data = await asyncio.to_thread(kpi_ws.get_all_values)
            mon_data = await asyncio.to_thread(mon_ws.get_all_values)

            self.cache = {"kpi": kpi_data, "monitoring": mon_data}
            self.last_update = datetime.now()

            logger.info(f"Кэш обновлён → KPI: {len(kpi_data)} строк, Monitoring: {len(mon_data)} строк")

            # === МАГИЯ ДЛЯ ЛОКАЛЬНОГО ДЕБАГА ===
            if not os.getenv("RENDER"):  # только локально
                try:
                    with open("cached_data.json", "w", encoding="utf-8") as f:
                        json.dump(self.cache, f, ensure_ascii=False, indent=2)
                    logger.info("Локально сохранён cached_data.json (для дебага)")
                except Exception as e:
                    logger.warning(f"Не удалось записать cached_data.json: {e}")

            return True

        except Exception as e:
            logger.error(f"Ошибка при обновлении кэша из Google Sheets: {e}")
            return False

    def get_user_data(self, sheet_type: str, username: str):
        """Синхронный метод — используется в хендлерах"""
        if not username:
            return None

        rows = self.cache.get(sheet_type, [])
        search = username.strip().lstrip('@').lower()

        for row in rows:
            if row and len(row) > 0:
                cell = str(row[0]).strip().lstrip('@').lower()
                if cell == search:
                    return row
        return None

    def get_last_update(self):
        return self.last_update
