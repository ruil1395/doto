import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found! Create .env file with BOT_TOKEN=your_token")

ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

MESSAGES = {
    "start": """
🎮 *Dota 2 Counter Bot*

Привет, {name}! Я помогу с контрпиками, билдами и предсказаниями.

*Команды:*
/hero [имя] — информация о герое
/counter [имя] — контрпики из базы
/counters [имя] — статистические контрпики (API)
/build [имя] — рекомендуемый билд
/stats [имя] — актуальная статистика
/meta — текущая мета
/predict [A] vs [B] — предсказать победителя
/search [запрос] — поиск героя
/list — список героев
/help — помощь

Просто напиши имя героя — и я найду всё о нём!
""",
    "help": """
📚 *Помощь по командам:*

*/hero [имя]* — полная информация о герое
*/counter [имя]* — контрпики из базы знаний
*/counters [имя]* — статистические контрпики (OpenDota API)
*/build [имя]* — рекомендуемый билд
*/stats [имя]* — актуальная статистика (винрейт, тир, мета-скор)
*/meta* — текущая мета (топ пиков, винрейтов, тренды)
*/predict [A] vs [B]* — ML-предсказание победителя
*/search [запрос]* — поиск по части имени
*/list* — список всех героев
*/about* — информация о боте

*Примеры:*
• `/hero kez`
• `/stats muerta`
• `/predict kez void slardar vs muerta ember tide`
• `/meta`

💡 *Совет:* Можно просто написать имя героя без команды!
"""
}
