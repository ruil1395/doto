from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.config import logger
from src.services.stats_service import StatsService
from src.services.hero_service import HeroService


class StatsHandlers:
    @staticmethod
    async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи имя героя: `/stats kez`\n"
                "Или используй `/meta` для общей статистики",
                parse_mode='Markdown'
            )
            return
            
        hero_name = " ".join(context.args)
        hero = HeroService.find_hero(hero_name)
        
        if not hero:
            await update.message.reply_text(
                f"❌ Герой '{hero_name}' не найден",
                parse_mode='Markdown'
            )
            return
            
        message = await update.message.reply_text("⏳ Загружаю статистику...")
        
        try:
            async with StatsService() as stats_service:
                stats = await stats_service.get_hero_stats(hero.name)
                
                if not stats:
                    await message.edit_text(
                        "❌ Не удалось загрузить статистику. Попробуй позже."
                    )
                    return
                    
                text = stats_service.format_stats_message(stats)
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data=f"stats:{hero.name}")],
                    [InlineKeyboardButton("🔙 Назад к герою", callback_data=f"hero:{hero.name}")]
                ])
                
                await message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
                
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
            await message.edit_text("❌ Ошибка загрузки статистики")
    
    @staticmethod
    async def meta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = await update.message.reply_text("⏳ Анализирую текущую мету...")
        
        try:
            async with StatsService() as stats_service:
                report = await stats_service.get_meta_report()
                
                if not report:
                    await message.edit_text(
                        "❌ Не удалось загрузить данные о мете. Попробуй позже."
                    )
                    return
                    
                text = stats_service.format_meta_message(report)
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data="meta:update")],
                    [InlineKeyboardButton("📋 Список героев", callback_data="list")]
                ])
                
                await message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
                
        except Exception as e:
            logger.error(f"Error loading meta: {e}")
            await message.edit_text("❌ Ошибка загрузки меты")
    
    @staticmethod
    async def counters_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи имя героя: `/counters kez`",
                parse_mode='Markdown'
            )
            return
            
        hero_name = " ".join(context.args)
        hero = HeroService.find_hero(hero_name)
        
        if not hero:
            await update.message.reply_text(f"❌ Герой '{hero_name}' не найден")
            return
            
        message = await update.message.reply_text("⏳ Анализирую матчапы...")
        
        try:
            async with StatsService() as stats_service:
                counters = await stats_service.get_counters_stats(hero.name)
                
                if not counters:
                    await message.edit_text(
                        "❌ Нет данных о матчапах. Попробуй позже."
                    )
                    return
                    
                lines = [
                    f"🛡️ *Статистические контрпики на {hero.name}:*",
                    "_На основе данных профессиональных матчей_",
                    ""
                ]
                
                for i, counter in enumerate(counters[:7], 1):
                    lines.append(
                        f"{i}. *{counter['hero']}*\n"
                        f"   Винрейт против: {counter['win_rate']:.1f}%\n"
                        f"   {counter['advantage']}"
                    )
                    
                text = "\n".join(lines)
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"hero:{hero.name}")]
                ])
                
                await message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
                
        except Exception as e:
            logger.error(f"Error loading counters: {e}")
            await message.edit_text("❌ Ошибка загрузки данных")
