from telegram import Update
from telegram.ext import ContextTypes
from src.config import MESSAGES, logger
from src.services.hero_service import HeroService


class CommandHandlers:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started bot")
        
        text = MESSAGES["start"].format(name=user.first_name)
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(MESSAGES["help"], parse_mode='Markdown')
    
    @staticmethod
    async def list_heroes(update: Update, context: ContextTypes.DEFAULT_TYPE):
        heroes = HeroService.get_all_heroes()
        
        by_role = {}
        for hero in heroes:
            main_role = hero.roles[0]
            by_role.setdefault(main_role, []).append(hero.name)
        
        lines = ["📋 *Герои в базе:*\n"]
        for role, names in sorted(by_role.items()):
            lines.append(f"*{role}:* {', '.join(sorted(names))}")
        
        text = "\n".join(lines)
        
        if len(text) > 4000:
            parts = []
            current = ""
            for line in lines:
                if len(current) + len(line) > 4000:
                    parts.append(current)
                    current = line + "\n"
                else:
                    current += line + "\n"
            if current:
                parts.append(current)
            
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
        heroes_count = len(HeroService.get_all_heroes())
        text = f"""
🤖 *Dota 2 Counter Bot*

Версия: 2.0 с ML-предсказаниями
Героев в базе: {heroes_count}
Функции:
• Контрпики и билды
• Актуальная статистика (OpenDota API)
• ML-предсказание матчей
• Анализ меты

Использует: Python, python-telegram-bot, OpenDota API
"""
        await update.message.reply_text(text, parse_mode='Markdown')
