# keep_alive.py
import threading
import time
import os
import requests

def keep_alive():
    url = os.getenv("RENDER_EXTERNAL_URL")  # или просто твой URL бота
    if not url:
        return

    def ping():
        while True:
            try:
                requests.get(url, timeout=10)
                print(f"[{time.strftime('%H:%M:%S')}] Пинг отправлен → {url}")
            except:
                pass
            time.sleep(300)  # каждые 5 минут

    thread = threading.Thread(target=ping, daemon=True)
    thread.start()

    print("Keep-alive пингер запущен (каждые 5 минут)")