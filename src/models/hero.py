from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HeroStats:
    win_rate: Optional[float] = None
    pick_rate: Optional[float] = None
    tier: Optional[str] = None


@dataclass
class HeroBuild:
    starting_items: List[str] = field(default_factory=list)
    early_game: List[str] = field(default_factory=list)
    mid_game: List[str] = field(default_factory=list)
    late_game: List[str] = field(default_factory=list)
    situational: List[str] = field(default_factory=list)


@dataclass
class HeroCounters:
    strong_against: List[str] = field(default_factory=list)
    weak_against: List[str] = field(default_factory=list)
    counter_items: List[str] = field(default_factory=list)
    core_items: List[str] = field(default_factory=list)
    countered_by: dict = field(default_factory=dict)


@dataclass
class Hero:
    id: str
    name: str
    localized_name: Optional[str] = None
    primary_attr: str = "str"
    attack_type: str = "Melee"
    roles: List[str] = field(default_factory=list)
    description: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    counters: HeroCounters = field(default_factory=HeroCounters)
    builds: Optional[HeroBuild] = None
    stats: Optional[HeroStats] = None
    
    def __post_init__(self):
        if self.localized_name is None:
            self.localized_name = self.name
