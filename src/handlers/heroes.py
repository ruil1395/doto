from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.config import logger, MESSAGES
from src.services.hero_service import HeroService


class HeroHandlers:
    @staticmethod
    def _create_hero_keyboard(hero_name: str) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("🛡️ Контрпики", callback_data=f"counter:{hero_name}"),
                InlineKeyboardButton("⚔️ Билд", callback_data=f"build:{hero_name}")
            ],
            [
                InlineKeyboardButton("📊 Статистика", callback_data=f"stats:{hero_name}"),
                InlineKeyboardButton("🔄 Другие герои", callback_data="list")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    async def hero_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи имя героя: `/hero kez`",
                parse_mode='Markdown'
            )
            return
        
        query = " ".join(context.args)
        await HeroHandlers._show_hero(update, context, query)
    
    @staticmethod
    async def counter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи имя героя: `/counter muerta`",
                parse_mode='Markdown'
            )
            return
        
        query = " ".join(context.args)
        hero = HeroService.find_hero(query)
        
        if not hero:
            await HeroHandlers._handle_not_found(update, query)
            return
        
        text = HeroService.format_counters(hero)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад к герою", callback_data=f"hero:{hero.name}")
        ]])
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    @staticmethod
    async def build_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи имя героя: `/build void spirit`",
                parse_mode='Markdown'
            )
            return
        
        query = " ".join(context.args)
        hero = HeroService.find_hero(query)
        
        if not hero:
            await HeroHandlers._handle_not_found(update, query)
            return
        
        text = HeroService.format_build(hero)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад к герою", callback_data=f"hero:{hero.name}")
        ]])
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    @staticmethod
    async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи запрос: `/search void`",
                parse_mode='Markdown'
            )
            return
        
        query = " ".join(context.args)
        matches = HeroService.search_heroes(query)
        
        if not matches:
            await update.message.reply_text(
                f"❌ По запросу '*{query}*' ничего не найдено.",
                parse_mode='Markdown'
            )
            return
        
        if len(matches) == 1:
            await HeroHandlers._show_hero(update, context, matches[0].name)
            return
        
        keyboard = []
        for hero in matches:
            keyboard.append([InlineKeyboardButton(hero.name, callback_data=f"hero:{hero.name}")])
        
        text = f"🔍 Найдено по запросу '*{query}*':"
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        
        if text.startswith('/'):
            return
        
        hero = HeroService.find_hero(text)
        
        if hero:
            await HeroHandlers._show_hero(update, context, text, is_callback=False)
            return
        
        matches = HeroService.search_heroes(text)
        if matches:
            if len(matches) == 1:
                await HeroHandlers._show_hero(update, context, matches[0].name, is_callback=False)
            else:
                keyboard = [[InlineKeyboardButton(h.name, callback_data=f"hero:{h.name}")] 
                           for h in matches[:5]]
                await update.message.reply_text(
                    f"🤔 Несколько вариантов по '*{text}*':",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            await update.message.reply_text(
                f"❓ Не нашел '*{text}*'. Используй `/search {text}` или `/list`",
                parse_mode='Markdown'
            )
    
    @staticmethod
    async def _show_hero(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                        query: str, is_callback: bool = False):
        hero = HeroService.find_hero(query)
        
        if not hero:
            await HeroHandlers._handle_not_found(update, query)
            return
        
        text = HeroService.format_hero_info(hero)
        keyboard = HeroHandlers._create_hero_keyboard(hero.name)
        
        if is_callback:
            await update.callback_query.edit_message_text(
                text, parse_mode='Markdown', reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                text, parse_mode='Markdown', reply_markup=keyboard
            )
    
    @staticmethod
    async def _handle_not_found(update: Update, query: str):
        matches = HeroService.search_heroes(query)
        
        if matches:
            suggestions = ", ".join([h.name for h in matches[:3]])
            text = f"❌ Герой '*{query}*' не найден.\n\nВозможно: {suggestions}?"
        else:
            text = MESSAGES["hero_not_found"].format(query=query)
        
        await update.message.reply_text(text, parse_mode='Markdown')
