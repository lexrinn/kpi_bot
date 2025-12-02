# app/services/data_manager.py
import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = "cached_data.json"

class DataManager:
    def __init__(self):
        self.client = None

    def _authenticate(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        # Из переменной окружения (для деплоя)
        creds_json_str = os.getenv('GOOGLE_CREDS_JSON')
        if creds_json_str:
            try:
                creds = json.loads(creds_json_str)
                return gspread.authorize(Credentials.from_service_account_info(creds, scopes=scopes))
            except Exception as e:
                print(f"Ошибка GOOGLE_CREDS_JSON: {e}")

        # Локальный файл creds.json
        key_file = os.getenv('GOOGLE_KEY_FILE', 'creds.json')
        if os.path.exists(key_file):
            try:
                return gspread.authorize(Credentials.from_service_account_file(key_file, scopes=scopes))
            except Exception as e:
                print(f"Ошибка чтения creds.json: {e}")

        print("Не удалось авторизоваться в Google")
        return None

    def update_cache(self):
        print(f"CREDS: {os.getenv('GOOGLE_CREDS_JSON')[:100]}...")  # первые 100 символов
        sheet_name = os.getenv('GOOGLE_SHEET_NAME')
        print(f"Обновляю кэш из таблицы: '{sheet_name}'")

        if not sheet_name:
            print("ОШИБКА: не указан GOOGLE_SHEET_NAME")
            return False

        if not self.client:
            self.client = self._authenticate()
            if not self.client:
                return False

        try:
            spreadsheet = self.client.open(sheet_name)
            print(f"Таблица открыта: {spreadsheet.title}")

            kpi_data = spreadsheet.worksheet('kpi').get_all_values()
            mon_data = spreadsheet.worksheet('monitoring').get_all_values()

            print(f"kpi: {len(kpi_data)} строк, monitoring: {len(mon_data)} строк")

            full_data = {"kpi": kpi_data, "monitoring": mon_data}

            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)

            print("КЭШ УСПЕШНО СОХРАНЁН В cached_data.json")
            return True

        except Exception as e:
            print(f"ОШИБКА при чтении таблицы: {e}")
            return False

    def get_user_data(self, sheet_type: str, username: str):
        if not os.path.exists(DATA_FILE):
            return "NoCache"

        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            rows = data.get(sheet_type, [])
            search = username.strip().lower().replace('@', '')

            for row in rows:
                if row and len(row) > 0:
                    if str(row[0]).strip().lower().replace('@', '') == search:
                        return row
            return None
        except Exception as e:
            logging.error(f"Ошибка чтения кэша: {e}")

            return "Error"
