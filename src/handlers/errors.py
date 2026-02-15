import traceback
from telegram import Update
from telegram.ext import ContextTypes
from src.config import logger, ADMIN_IDS


class ErrorHandlers:
    @staticmethod
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Exception while handling an update: {context.error}")
        logger.error(traceback.format_exc())
        
        if ADMIN_IDS:
            error_text = f"""
❌ *Ошибка в боте:*
