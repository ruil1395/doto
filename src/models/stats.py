from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class HeroStats:
    hero_id: int
    hero_name: str
    win_rate: float = 0.0
    pick_rate: float = 0.0
    ban_rate: float = 0.0
    win_rate_herald: Optional[float] = None
    win_rate_divine: Optional[float] = None
    win_rate_pro: Optional[float] = None
    win_rate_trend: float = 0.0
    tier: str = "?"
    meta_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def get_tier_emoji(self) -> str:
        tiers = {"S": "🔴", "A": "🟠", "B": "🟡", "C": "🟢", "D": "⚪"}
        return tiers.get(self.tier, "❓")
    
    def format_win_rate(self, wr: Optional[float]) -> str:
        if wr is None:
            return "N/A"
        if wr >= 55:
            return f"🟢 {wr:.1f}%"
        elif wr >= 50:
            return f"🟡 {wr:.1f}%"
        elif wr >= 45:
            return f"🟠 {wr:.1f}%"
        else:
            return f"🔴 {wr:.1f}%"


@dataclass
class MatchupStats:
    hero_id: int
    vs_hero_id: int
    wins: int = 0
    losses: int = 0
    
    @property
    def games(self) -> int:
        return self.wins + self.losses
    
    @property
    def win_rate(self) -> float:
        if self.games == 0:
            return 0.0
        return (self.wins / self.games) * 100
    
    def get_advantage(self) -> str:
        if self.win_rate > 55:
            return "⬆️ Сильное преимущество"
        elif self.win_rate > 52:
            return "↗️ Небольшое преимущество"
        elif self.win_rate < 45:
            return "⬇️ Сильное disadvantage"
        elif self.win_rate < 48:
            return "↘️ Небольшое disadvantage"
        else:
            return "➡️ Нейтральный матчап"


@dataclass
class MetaReport:
    timestamp: datetime
    top_picks: List[HeroStats] = field(default_factory=list)
    top_wins: List[HeroStats] = field(default_factory=list)
    top_bans: List[HeroStats] = field(default_factory=list)
    rising_heroes: List[HeroStats] = field(default_factory=list)
    falling_heroes: List[HeroStats] = field(default_factory=list)
    patch: Optional[str] = None
