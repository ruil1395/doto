import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from src.api.opendota import OpenDotaAPI
from src.models.stats import HeroStats, MetaReport, MatchupStats

logger = logging.getLogger(__name__)


class StatsService:
    def __init__(self, cache_ttl: int = 3600):
        self.api = OpenDotaAPI(cache_ttl=cache_ttl)
        self._hero_stats_cache: Dict[str, HeroStats] = {}
        self._meta_cache: Optional[MetaReport] = None
        self._cache_time: Optional[datetime] = None
        
    async def __aenter__(self):
        await self.api.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.api.__aexit__(exc_type, exc_val, exc_tb)
        
    def _is_cache_valid(self) -> bool:
        if not self._cache_time:
            return False
        return datetime.now() - self._cache_time < timedelta(seconds=self.api.cache_ttl)
        
    async def get_hero_stats(self, hero_name: str, force_update: bool = False) -> Optional[HeroStats]:
        if not force_update and hero_name in self._hero_stats_cache and self._is_cache_valid():
            return self._hero_stats_cache[hero_name]
            
        hero_id = self._get_hero_id(hero_name)
        if not hero_id:
            return None
            
        stats = await self.api.get_hero_stats_detailed(hero_id)
        if stats:
            self._hero_stats_cache[hero_name] = stats
            
        return stats
        
    async def get_meta_report(self, force_update: bool = False) -> Optional[MetaReport]:
        if not force_update and self._meta_cache and self._is_cache_valid():
            return self._meta_cache
            
        report = await self.api.get_meta_report()
        if report:
            self._meta_cache = report
            self._cache_time = datetime.now()
            
        return report
        
    async def get_counters_stats(self, hero_name: str) -> List[Dict]:
        hero_id = self._get_hero_id(hero_name)
        if not hero_id:
            return []
            
        matchups = await self.api.get_best_counters(hero_id)
        
        results = []
        for m in matchups:
            vs_hero = self._get_hero_name_by_id(m.vs_hero_id)
            if vs_hero:
                results.append({
                    "hero": vs_hero,
                    "win_rate": m.win_rate,
                    "games": m.games,
                    "advantage": m.get_advantage()
                })
                
        return results
        
    def _get_hero_id(self, hero_name: str) -> Optional[int]:
        hero_key = hero_name.lower().replace(" ", "_").replace("-", "_")
        
        hero_id_map = {
            "kez": 145,
            "muerta": 138,
            "void_spirit": 126,
            "ember_spirit": 106,
            "slardar": 28,
            "tidehunter": 29,
            "shadow_shaman": 27,
            "lich": 31,
            "lion": 26,
            "phantom_lancer": 12,
            "anti_mage": 1,
        }
        
        return hero_id_map.get(hero_key)
        
    def _get_hero_name_by_id(self, hero_id: int) -> Optional[str]:
        reverse_map = {
            145: "Kez",
            138: "Muerta",
            126: "Void Spirit",
            106: "Ember Spirit",
            28: "Slardar",
            29: "Tidehunter",
            27: "Shadow Shaman",
            31: "Lich",
            26: "Lion",
            12: "Phantom Lancer",
            1: "Anti-Mage",
        }
        return reverse_map.get(hero_id)
        
    def format_stats_message(self, stats: HeroStats) -> str:
        lines = [
            f"📊 *Статистика {stats.hero_name}*",
            "",
            f"{stats.get_tier_emoji()} *Тир:* {stats.tier}",
            f"📈 *Винрейт:* {stats.format_win_rate(stats.win_rate)}",
            f"🎯 *Пикрейт:* {stats.pick_rate} игр",
        ]
        
        if stats.ban_rate:
            lines.append(f"🚫 *Банрейт:* {stats.ban_rate} игр")
            
        lines.append(f"⭐ *Мета-скор:* {stats.meta_score:.1f}/100")
        
        lines.extend(["", "*Винрейт по рангам:*"])
        if stats.win_rate_herald:
            lines.append(f"  🥉 Herald: {stats.format_win_rate(stats.win_rate_herald)}")
        if stats.win_rate_divine:
            lines.append(f"  🥇 Divine+: {stats.format_win_rate(stats.win_rate_divine)}")
        if stats.win_rate_pro:
            lines.append(f"  🏆 Pro: {stats.format_win_rate(stats.win_rate_pro)}")
            
        lines.extend([
            "",
            f"_Обновлено: {stats.last_updated.strftime('%H:%M')}_"
        ])
        
        return "\n".join(lines)
        
    def format_meta_message(self, report: MetaReport) -> str:
        lines = [
            "🌍 *Текущая мета*",
            f"_Обновлено: {report.timestamp.strftime('%d.%m %H:%M')}_",
            "",
            "🔥 *Топ по винрейту:*"
        ]
        
        for i, hero in enumerate(report.top_wins[:5], 1):
            lines.append(f"{i}. {hero.hero_name} {hero.format_win_rate(hero.win_rate)}")
            
        lines.extend(["", "📈 *Самые популярные:*"])
        for i, hero in enumerate(report.top_picks[:5], 1):
            lines.append(f"{i}. {hero.hero_name} ({hero.pick_rate} пиков)")
            
        if report.rising_heroes:
            lines.extend(["", "⬆️ *Растут винрейтом:*"])
            for hero in report.rising_heroes[:3]:
                lines.append(f"• {hero.hero_name} {hero.format_win_rate(hero.win_rate)}")
                
        return "\n".join(lines)
