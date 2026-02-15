import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загрузка .env
load_dotenv()

# Пути
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Токен (обязательно!)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN or ":" not in BOT_TOKEN:
    logging.error("Invalid BOT_TOKEN!")
    # Не выходим, чтобы логи были видны

# Админы
ADMIN_IDS = []
try:
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
except:
    pass

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Сообщения
MESSAGES = {
    "start": """🎮 *Dota 2 Counter Bot*

Привет, {name}!

*Команды:*
/hero [имя] — информация о герое
/predict [A] vs [B] — предсказать победителя
/stats [имя] — статистика
/meta — текущая мета
/list — список героев

Просто напиши имя героя!""",

    "help": """📚 *Команды:*

/hero [имя] — информация о герое
/counter [имя] — контрпики
/predict [A] vs [B] — ML-предсказание
/stats [имя] — винрейт, тир
/meta — топ пиков
/search [запрос] — поиск
/list — все герои""",

    "hero_not_found": "❌ Герой '{query}' не найден"
}
