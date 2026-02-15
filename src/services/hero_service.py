from typing import List, Optional, Tuple
from src.models.hero import Hero
from src.data.heroes_db import HEROES_DATABASE, HEROES_BY_NAME


class HeroService:
    @staticmethod
    def find_hero(query: str) -> Optional[Hero]:
        query = query.lower().strip().replace(" ", "_").replace("-", "_")
        return HEROES_BY_NAME.get(query)
    
    @staticmethod
    def search_heroes(query: str, limit: int = 5) -> List[Hero]:
        query = query.lower()
        matches = []
        
        for hero in HEROES_DATABASE.values():
            search_terms = [
                hero.id,
                hero.name.lower(),
                hero.localized_name.lower() if hero.localized_name else "",
                hero.name.lower().replace(" ", ""),
                hero.name.lower().replace("-", ""),
            ]
            
            if any(query in term for term in search_terms if term):
                matches.append(hero)
                
            if len(matches) >= limit:
                break
                
        return matches
    
    @staticmethod
    def get_all_heroes() -> List[Hero]:
        return list(HEROES_DATABASE.values())
    
    @staticmethod
    def format_hero_info(hero: Hero) -> str:
        lines = [
            f"🎯 *{hero.name}*",
            f"📊 Роль: {', '.join(hero.roles)}",
            f"⚔️ Атака: {hero.attack_type} | Атрибут: {hero.primary_attr.upper()}",
            "",
            f"📝 *Описание:*\n{hero.description}",
            "",
            "✅ *Сильные стороны:*"
        ]
        
        for strength in hero.strengths:
            lines.append(f"  • {strength}")
            
        lines.extend(["", "❌ *Слабости:*"])
        for weakness in hero.weaknesses:
            lines.append(f"  • {weakness}")
            
        if hero.stats:
            lines.extend([
                "",
                f"📈 Статистика: WR {hero.stats.win_rate}% | Pick {hero.stats.pick_rate}% | Tier {hero.stats.tier}"
            ])
            
        return "\n".join(lines)
    
    @staticmethod
    def format_counters(hero: Hero) -> str:
        lines = [
            f"🛡️ *Контрпики на {hero.name}:*",
            "",
            f"💡 *{hero.counters.countered_by.get('description', '')}*",
            "",
            "⚔️ *Герои-контрпики:*"
        ]
        
        for i, counter in enumerate(hero.counters.countered_by.get('heroes', []), 1):
            lines.append(f"{i}. {counter}")
            
        lines.extend(["", "🎒 *Контр-предметы:*"])
        for item in hero.counters.countered_by.get('items', []):
            lines.append(f"  • {item}")
            
        return "\n".join(lines)
    
    @staticmethod
    def format_build(hero: Hero) -> str:
        if not hero.builds:
            return "Билд не найден"
            
        build = hero.builds
        lines = [
            f"⚔️ *Билд для {hero.name}:*",
            "",
            "🌱 *Старт:*",
            f"  {', '.join(build.starting_items)}",
            "",
            "⚡ *Ранняя игра:*",
            f"  {' → '.join(build.early_game)}",
            "",
            "🔥 *Середина игры:*",
            f"  {' → '.join(build.mid_game)}",
            "",
            "👑 *Лейт:*",
            f"  {' → '.join(build.late_game)}",
        ]
        
        if build.situational:
            lines.extend([
                "",
                "🔄 *Ситуативно:*",
                f"  {', '.join(build.situational)}"
            ])
            
        return "\n".join(lines)
