from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.config import logger
from src.services.hero_service import HeroService
from src.services.stats_service import StatsService
from src.handlers.heroes import HeroHandlers
from src.handlers.predict import PredictionHandlers


class CallbackHandlers:
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"Callback: {data}")
        
        try:
            if data.startswith("hero:"):
                hero_name = data.split(":", 1)[1]
                await HeroHandlers._show_hero(update, context, hero_name, is_callback=True)
                
            elif data.startswith("counter:"):
                hero_name = data.split(":", 1)[1]
                await CallbackHandlers._show_counter(update, hero_name)
                
            elif data.startswith("build:"):
                hero_name = data.split(":", 1)[1]
                await CallbackHandlers._show_build(update, hero_name)
                
            elif data.startswith("stats:"):
                hero_name = data.split(":", 1)[1]
                await CallbackHandlers._show_stats(update, hero_name)
                
            elif data.startswith("meta"):
                await CallbackHandlers._show_meta(update)
                
            elif data.startswith("predict_details:"):
                await PredictionHandlers(None).show_details(update, context)
                
            elif data == "predict_new":
                await query.edit_message_text(
                    "🔮 Введи новое предсказание:\n`/predict [свет] vs [тьма]`",
                    parse_mode='Markdown'
                )
                
            elif data.startswith("predict_back:"):
                parts = data.split(":")
                if len(parts) >= 3:
                    radiant = parts[1].split(",")
                    dire = parts[2].split(",")
                    await PredictionHandlers(None)._make_prediction(update, radiant, dire, query.message)
                
            elif data == "list":
                await CallbackHandlers._show_list(update)
                
        except Exception as e:
            logger.error(f"Callback error: {e}")
            await query.edit_message_text("❌ Ошибка")
    
    @staticmethod
    async def _show_counter(update: Update, hero_name: str):
        hero = HeroService.find_hero(hero_name)
        if not hero:
            return
            
        text = HeroService.format_counters(hero)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data=f"hero:{hero.name}")
        ]])
        
        await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    @staticmethod
    async def _show_build(update: Update, hero_name: str):
        hero = HeroService.find_hero(hero_name)
        if not hero:
            return
            
        text = HeroService.format_build(hero)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data=f"hero:{hero.name}")
        ]])
        
        await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    @staticmethod
    async def _show_stats(update: Update, hero_name: str):
        message = update.callback_query.message
        await message.edit_text("⏳ Обновляю статистику...")
        
        try:
            async with StatsService() as service:
                stats = await service.get_hero_stats(hero_name, force_update=True)
                
                if not stats:
                    await message.edit_text("❌ Не удалось загрузить")
                    return
                    
                text = service.format_stats_message(stats)
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data=f"stats:{hero_name}")],
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"hero:{hero_name}")]
                ])
                
                await message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error: {e}")
            await message.edit_text("❌ Ошибка")
    
    @staticmethod
    async def _show_meta(update: Update):
        message = update.callback_query.message
        await message.edit_text("⏳ Обновляю мету...")
        
        try:
            async with StatsService() as service:
                report = await service.get_meta_report(force_update=True)
                
                if not report:
                    await message.edit_text("❌ Не удалось загрузить")
                    return
                    
                text = service.format_meta_message(report)
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data="meta:update")],
                    [InlineKeyboardButton("📋 Герои", callback_data="list")]
                ])
                
                await message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error: {e}")
            await message.edit_text("❌ Ошибка")
    
    @staticmethod
    async def _show_list(update: Update):
        heroes = HeroService.get_all_heroes()
        roles = {}
        
        for hero in heroes:
            main_role = hero.roles[0]
            roles.setdefault(main_role, []).append(hero.name)
        
        keyboard = []
        for role, names in sorted(roles.items())[:6]:
            row = []
            for name in sorted(names)[:3]:
                row.append(InlineKeyboardButton(name, callback_data=f"hero:{name}"))
            if row:
                keyboard.append(row)
        
        await update.callback_query.edit_message_text(
            "📋 *Выбери героя:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
