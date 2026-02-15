import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from src.models.stats import HeroStats, MatchupStats, MetaReport

logger = logging.getLogger(__name__)


class OpenDotaAPI:
    BASE_URL = "https://api.opendota.com/api"
    
    def __init__(self, cache_ttl: int = 3600):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "Dota2CounterBot/1.0"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def _get_cache(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        cached_time = self._cache_time.get(key)
        if cached_time and datetime.now() - cached_time > timedelta(seconds=self.cache_ttl):
            del self._cache[key]
            del self._cache_time[key]
            return None
        return self._cache[key]
        
    def _set_cache(self, key: str, value: Any):
        self._cache[key] = value
        self._cache_time[key] = datetime.now()
        
    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Any]:
        cache_key = f"{endpoint}:{str(params)}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
            
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self._set_cache(cache_key, data)
                    return data
                elif response.status == 429:
                    logger.warning("Rate limit exceeded, waiting...")
                    await asyncio.sleep(1)
                    return await self._request(endpoint, params)
                else:
                    logger.error(f"API error {response.status}: {await response.text()}")
                    return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
            
    async def get_hero_stats(self) -> Optional[List[Dict]]:
        return await self._request("heroStats")
        
    async def get_hero_matchups(self, hero_id: int) -> Optional[List[Dict]]:
        return await self._request(f"heroes/{hero_id}/matchups")
        
    async def get_hero_stats_detailed(self, hero_id: int) -> Optional[HeroStats]:
        stats_list = await self.get_hero_stats()
        if not stats_list:
            return None
            
        for stat in stats_list:
            if stat.get("id") == hero_id:
                return self._parse_hero_stats(stat)
        return None
        
    def _parse_hero_stats(self, data: Dict) -> HeroStats:
        pro_win = data.get("pro_win", 0)
        pro_pick = data.get("pro_pick", 1)
        pro_win_rate = (pro_win / pro_pick * 100) if pro_pick > 0 else 0
        
        tier = self._calculate_tier(pro_win_rate, data.get("pro_pick", 0))
        
        return HeroStats(
            hero_id=data.get("id", 0),
            hero_name=data.get("localized_name", "Unknown"),
            win_rate=pro_win_rate,
            pick_rate=data.get("pro_pick", 0),
            ban_rate=data.get("pro_ban", 0),
            win_rate_herald=self._safe_percent(data.get("1_win"), data.get("1_pick")),
            win_rate_divine=self._safe_percent(data.get("7_win"), data.get("7_pick")),
            win_rate_pro=pro_win_rate,
            tier=tier,
            meta_score=self._calculate_meta_score(data),
            last_updated=datetime.now()
        )
        
    def _safe_percent(self, wins: Optional[int], picks: Optional[int]) -> Optional[float]:
        if wins is None or picks is None or picks == 0:
            return None
        return (wins / picks) * 100
        
    def _calculate_tier(self, win_rate: float, pick_rate: int) -> str:
        if win_rate >= 55 and pick_rate > 100:
            return "S"
        elif win_rate >= 52 or (win_rate >= 50 and pick_rate > 200):
            return "A"
        elif win_rate >= 48:
            return "B"
        elif win_rate >= 45:
            return "C"
        else:
            return "D"
            
    def _calculate_meta_score(self, data: Dict) -> float:
        pro_win = data.get("pro_win", 0)
        pro_pick = data.get("pro_pick", 1)
        pro_ban = data.get("pro_ban", 0)
        
        if pro_pick == 0:
            return 0.0
            
        win_rate = (pro_win / pro_pick) * 100
        popularity = min(pro_pick / 50, 10)
        
        return (win_rate * 0.6) + (popularity * 4)
        
    async def get_meta_report(self, min_games: int = 50) -> Optional[MetaReport]:
        stats = await self.get_hero_stats()
        if not stats:
            return None
            
        heroes = [self._parse_hero_stats(h) for h in stats if h.get("pro_pick", 0) >= min_games]
        
        if not heroes:
            return None
            
        by_win = sorted(heroes, key=lambda x: x.win_rate, reverse=True)[:10]
        by_pick = sorted(heroes, key=lambda x: x.pick_rate, reverse=True)[:10]
        by_ban = sorted(heroes, key=lambda x: x.ban_rate, reverse=True)[:10]
        
        rising = [h for h in heroes if h.win_rate > 55][:5]
        falling = [h for h in heroes if h.win_rate < 45][:5]
        
        return MetaReport(
            timestamp=datetime.now(),
            top_picks=by_pick,
            top_wins=by_win,
            top_bans=by_ban,
            rising_heroes=rising,
            falling_heroes=falling
        )
        
    async def get_best_counters(self, hero_id: int, min_games: int = 20) -> List[MatchupStats]:
        matchups = await self.get_hero_matchups(hero_id)
        if not matchups:
            return []
            
        results = []
        for m in matchups:
            games = m.get("games_played", 0)
            if games < min_games:
                continue
                
            wins = m.get("wins", 0)
            results.append(MatchupStats(
                hero_id=hero_id,
                vs_hero_id=m.get("hero_id", 0),
                wins=wins,
                losses=games - wins
            ))
            
        results.sort(key=lambda x: x.win_rate)
        return results[:10]
