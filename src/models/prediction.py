from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime


class PredictionResult(Enum):
    RADIANT_WIN = "radiant_win"
    DIRE_WIN = "dire_win"
    UNCERTAIN = "uncertain"


@dataclass
class TeamAnalysis:
    team_name: str
    heroes: List[str]
    synergy_score: float = 0.0
    draft_score: float = 0.0
    meta_score: float = 0.0
    win_probability: float = 0.0
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    key_heroes: List[str] = field(default_factory=list)


@dataclass
class MatchPrediction:
    radiant: TeamAnalysis
    dire: TeamAnalysis
    result: PredictionResult
    confidence: float
    win_probability_radiant: float
    win_probability_dire: float
    key_factors: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    lane_matchups: List[Dict] = field(default_factory=list)
    counter_matchups: List[Dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_winner_text(self) -> str:
        if self.result == PredictionResult.RADIANT_WIN:
            return f"🟢 Сторона Света ({self.win_probability_radiant:.1f}%)"
        elif self.result == PredictionResult.DIRE_WIN:
            return f"🔴 Сторона Тьмы ({self.win_probability_dire:.1f}%)"
        else:
            return "⚪ Неопределенно (50/50)"
    
    def get_confidence_text(self) -> str:
        if self.confidence >= 80:
            return "🔴 Очень высокая"
        elif self.confidence >= 65:
            return "🟠 Высокая"
        elif self.confidence >= 50:
            return "🟡 Средняя"
        else:
            return "🟢 Низкая (равные шансы)"


@dataclass
class DraftState:
    radiant_picks: List[str] = field(default_factory=list)
    radiant_bans: List[str] = field(default_factory=list)
    dire_picks: List[str] = field(default_factory=list)
    dire_bans: List[str] = field(default_factory=list)
    phase: str = "pick"
    
    def is_complete(self) -> bool:
        return len(self.radiant_picks) >= 5 and len(self.dire_picks) >= 5
