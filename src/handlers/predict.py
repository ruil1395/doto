from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import List, Tuple, Dict
from src.config import logger
from src.ml.predictor import MatchPredictor
from src.services.hero_service import HeroService


class PredictionHandlers:
    def __init__(self):
        self.draft_states: Dict[int, dict] = {}
        
    async def predict_quick(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрое предсказание - /predict [ radiant ] vs [ dire ]"""
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи составы: `/predict kez void slardar shaman lich vs muerta ember tide lion pudge`",
                parse_mode='Markdown'
            )
            return
            
        args = " ".join(context.args).lower()
        
        if " vs " not in args and " против " not in args:
            await update.message.reply_text(
                "❌ Раздели команды словом `vs` или `против`",
                parse_mode='Markdown'
            )
            return
            
        separator = " vs " if " vs " in args else " против "
        parts = args.split(separator)
        
        if len(parts) != 2:
            await update.message.reply_text("❌ Нужно указать ровно 2 команды")
            return
            
        radiant_text = parts[0].strip()
        dire_text = parts[1].strip()
        
        radiant = [h.strip() for h in radiant_text.split() if h.strip()]
        dire = [h.strip() for h in dire_text.split() if h.strip()]
        
        valid_rad, errors_rad = self._validate_heroes(radiant)
        valid_dire, errors_dire = self._validate_heroes(dire)
        
        if errors_rad or errors_dire:
            text = "❌ *Ошибки в названиях:*\n"
            for err in errors_rad + errors_dire:
                text += f"• {err}\n"
            await update.message.reply_text(text, parse_mode='Markdown')
            return
            
        await self._make_prediction(update, valid_rad, valid_dire)
        
    def _validate_heroes(self, heroes: List[str]) -> Tuple[List[str], List[str]]:
        valid = []
        errors = []
        
        for hero in heroes:
            found = HeroService.find_hero(hero)
            if found:
                valid.append(found.name)
            else:
                matches = HeroService.search_heroes(hero, limit=1)
                if matches:
                    valid.append(matches[0].name)
                else:
                    errors.append(f"'{hero}' не найден")
                    
        return valid, errors
        
    async def _make_prediction(
        self, 
        update: Update, 
        radiant: List[str], 
        dire: List[str],
        message=None
    ):
        target = message or update.message
        processing_msg = await target.reply_text("🔮 Анализирую составы...")
        
        try:
            predictor = MatchPredictor()
            prediction = await predictor.predict(radiant, dire)
            
            text = self._format_prediction(prediction)
            
            # Создаем callback data (ограничение 64 байта!)
            rad_str = ",".join(radiant)
            dire_str = ",".join(dire)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Детали", callback_data=f"predict_details:{rad_str}:{dire_str}")],
                [InlineKeyboardButton("🔄 Новый анализ", callback_data="predict_new")]
            ])
            
            await processing_msg.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            await processing_msg.edit_text("❌ Ошибка анализа. Попробуй позже.")
            
    def _format_prediction(self, pred) -> str:
        lines = [
            "🔮 *ПРЕДСКАЗАНИЕ МАТЧА*",
            "",
            f"🟢 *Сторона Света:* {', '.join(pred.radiant.heroes)}",
            f"🔴 *Сторона Тьмы:* {', '.join(pred.dire.heroes)}",
            "",
            f"🏆 *Вероятный победитель:*",
            f"{pred.get_winner_text()}",
            "",
            f"📊 *Уверенность:* {pred.get_confidence_text()} ({pred.confidence:.1f}%)",
            "",
            "*Ключевые факторы:*"
        ]
        
        for factor in pred.key_factors[:3]:
            lines.append(f"• {factor}")
            
        if pred.risk_factors:
            lines.extend(["", "*⚠️ Риски:*"])
            for risk in pred.risk_factors[:2]:
                lines.append(f"• {risk}")
                
        lines.extend([
            "",
            f"_Анализ: синергии, контрпики, мета, драфт_"
        ])
        
        return "\n".join(lines)
        
    async def show_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать детали предсказания"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split(":")
        if len(data) < 3:
            return
            
        radiant = data[1].split(",")
        dire = data[2].split(",")
        
        predictor = MatchPredictor()
        pred = await predictor.predict(radiant, dire)
        
        text = self._format_detailed_analysis(pred)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад", callback_data=f"predict_back:{','.join(radiant)}:{','.join(dire)}")]
        ])
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
        
    def _format_detailed_analysis(self, pred) -> str:
        lines = [
            f"📊 *Детальный анализ*",
            "",
            f"*🟢 Сторона Света ({pred.win_probability_radiant:.1f}%)*",
            f"Синергия: {pred.radiant.synergy_score:.0f}/100",
            f"Драфт: {pred.radiant.draft_score:.0f}/100",
            f"Мета: {pred.radiant.meta_score:.0f}/100",
        ]
        
        if pred.radiant.strengths:
            lines.append("\n*Сильные стороны:*")
            for s in pred.radiant.strengths[:3]:
                lines.append(f"  ✅ {s}")
                
        if pred.radiant.weaknesses:
            lines.append("\n*Слабости:*")
            for w in pred.radiant.weaknesses[:3]:
                lines.append(f"  ❌ {w}")
                
        lines.extend([
            "",
            f"*🔴 Сторона Тьмы ({pred.win_probability_dire:.1f}%)*",
            f"Синергия: {pred.dire.synergy_score:.0f}/100",
            f"Драфт: {pred.dire.draft_score:.0f}/100",
            f"Мета: {pred.dire.meta_score:.0f}/100",
        ])
        
        if pred.dire.strengths:
            lines.append("\n*Сильные стороны:*")
            for s in pred.dire.strengths[:3]:
                lines.append(f"  ✅ {s}")
                
        if pred.dire.weaknesses:
            lines.append("\n*Слабости:*")
            for w in pred.dire.weaknesses[:3]:
                lines.append(f"  ❌ {w}")
                
        if pred.counter_matchups:
            lines.extend(["", "*🎯 Ключевые матчапы:*"])
            for m in pred.counter_matchups[:4]:
                lines.append(f"  {m['text']}")
                
        return "\n".join(lines)
