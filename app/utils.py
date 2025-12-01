# app/utils.py

def get_kpi_indicator(value, metric: str):
    """Возвращает название цвета для KPI (Red/Yellow/Green/Blue/Purple/Unknown)"""
    try:
        clean = str(value).strip().replace('%', '').replace(',', '.').replace(' ', '')
        num = float(clean)
    except:
        return "Unknown"

    if metric == "CR":
        if num < 3.5:  return "Red"
        if num < 5.0:  return "Yellow"
        if num < 6.0:  return "Green"
        if num < 7.0:  return "Blue"
        return "Purple"
    if metric == "QA":
        if num < 80:   return "Red"
        if num < 90:   return "Yellow"
        if num < 95:   return "Green"
        if num < 98:   return "Blue"
        return "Purple"
    return "Unknown"


def get_bugs_indicator(time_str):
    """Возвращает название цвета для времени исправления багов"""
    try:
        h, m = map(int, str(time_str).split(':')[:2])
        minutes = h * 60 + m
        if minutes <= 120:  return "Green"
        if minutes <=300:  return "Yellow"
        return "Red"
    except:
        return "Unknown"


# Эмодзи-кружки для цветового отображения
COLOR_EMOJI = {
    "Red": "🔴",
    "Yellow": "🟡",
    "Green": "🟢",
    "Blue": "🔵",
    "Purple": "🟣",
    "Unknown": "❓"
}

# Стикеры для отправки
STICKERS = {
    "KPI": {
        "Red":    "CAACAgIAAxkBAAEL1d...",  # Вставь свои file_id!
        "Yellow": "CAACAgIAAxkBAAEL1d...",
        "Green":  "CAACAgIAAxkBAAEL1d...",
        "Blue":   "CAACAgIAAxkBAAEL1d...",
        "Purple": "CAACAgIAAxkBAAEL1d...",
    },
    "BUGS": {
        "Red":    "CAACAgIAAxkBAAEL1d...",
        "Yellow": "CAACAgIAAxkBAAEL1d...",
        "Green":  "CAACAgIAAxkBAAEL1d...",
    }
}


def get_emoji(indicator: str) -> str:
    """Возвращает цветовое кружок-эмодзи"""
    return COLOR_EMOJI.get(indicator, "❓")


def get_sticker(indicator: str, category: str) -> str | None:
    return STICKERS.get(category, {}).get(indicator)
