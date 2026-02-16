#!/usr/bin/env python3
"""
Dota 2 Counter Bot v2.1 - Extended Heroes + ML Predictor
"""

import asyncio
import logging
import sys
import os
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==================== КОНФИГУРАЦИЯ ====================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = []
try:
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
except:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== МОДЕЛИ ====================

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
    countered_by: Dict = field(default_factory=dict)

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
            return "🟢 Низкая"

# ==================== РАСШИРЕННАЯ БАЗА ГЕРОЕВ (30+ героев) ====================

HEROES_DATABASE = {
    # CARRY
    "kez": Hero(
        id="kez",
        name="Kez",
        localized_name="Kez",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Escape", "Nuker"],
        description="Мобильный agility-carry с двумя стилями боя.",
        strengths=["Высокая мобильность", "Взрывной урон", "Два режима атаки"],
        weaknesses=["Зависим от предметов", "Сложная механика", "Проблемы против иллюзий"],
        counters=HeroCounters(
            weak_against=["Phantom Lancer", "Chaos Knight", "Tidehunter", "Axe", "Puck"],
            counter_items=["Ghost Scepter", "Eul's Scepter", "Heaven's Halberd", "Force Staff", "Silver Edge"],
            countered_by={"heroes": ["Phantom Lancer", "Meepo", "Naga Siren"], "description": "Silver Edge брейкает пассивку"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Circlet", "Branches"],
            early_game=["Power Treads", "Magic Wand", "Echo Sabre"],
            mid_game=["Black King Bar", "Disperser", "Crystalys"],
            late_game=["Daedalus", "Satanic", "Butterfly", "Swift Blink"],
            situational=["Bloodthorn", "Monkey King Bar", "Abyssal Blade"]
        ),
        stats=HeroStats(win_rate=52.3, pick_rate=15.2, tier="A")
    ),
    
    "muerta": Hero(
        id="muerta",
        name="Muerta",
        localized_name="Muerta",
        primary_attr="int",
        attack_type="Ranged",
        roles=["Carry", "Nuker", "Disabler"],
        description="Гибридный carry с формой призрака.",
        strengths=["Огромный урон в лейте", "Форма призрака", "Смешанный урон"],
        weaknesses=["Медленный фарм", "Уязвима до BKB", "Контрится silence"],
        counters=HeroCounters(
            weak_against=["Anti-Mage", "Nyx Assassin", "Silencer", "Phantom Assassin"],
            counter_items=["Bloodthorn", "Silver Edge", "Orchid Malevolence", "Scythe of Vyse"],
            countered_by={"heroes": ["Anti-Mage", "Silencer"], "description": "Silencer отключает способности"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Circlet", "Branches"],
            early_game=["Power Treads", "Magic Wand", "Maelstrom"],
            mid_game=["Black King Bar", "Gleipnir", "Dragon Lance"],
            late_game=["Daedalus", "Satanic", "Bloodthorn", "Hurricane Pike"],
            situational=["Monkey King Bar", "Silver Edge"]
        ),
        stats=HeroStats(win_rate=51.8, pick_rate=12.5, tier="A")
    ),
    
    "phantom_lancer": Hero(
        id="phantom_lancer",
        name="Phantom Lancer",
        localized_name="Phantom Lancer",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Escape", "Pusher"],
        description="Carry с армией иллюзий. Сильнейший лейт.",
        strengths=["Армия иллюзий", "Высокая мобильность", "Сложно найти настоящего"],
        weaknesses=["Слаб рано", "Уязвим к AoE", "Требует фарма"],
        counters=HeroCounters(
            weak_against=["Axe", "Earthshaker", "Sven", "Medusa"],
            counter_items=["Battle Fury", "Mjollnir", "Radiance", "Shiva's Guard"],
            countered_by={"heroes": ["Axe", "Earthshaker"], "description": "AoE урон уничтожает иллюзии"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Quelling Blade", "Circlet", "Branches"],
            early_game=["Power Treads", "Wraith Band", "Diffusal Blade"],
            mid_game=["Manta Style", "Heart of Tarrasque", "Butterfly"],
            late_game=["Satanic", "Bloodthorn", "Skadi", "Boots of Travel"],
            situational=["Black King Bar", "Silver Edge"]
        ),
        stats=HeroStats(win_rate=53.2, pick_rate=9.8, tier="S")
    ),
    
    "anti_mage": Hero(
        id="anti_mage",
        name="Anti-Mage",
        localized_name="Anti-Mage",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Escape", "Nuker"],
        description="Быстрый фармер с мана-бёрном.",
        strengths=["Быстрый фарм", "Мана Break", "Blink для escape"],
        weaknesses=["Слаб рано", "Требует много фарма", "Уязвим к контролю"],
        counters=HeroCounters(
            weak_against=["Phantom Assassin", "Legion Commander", "Meepo", "Chaos Knight"],
            counter_items=["Silver Edge", "Bloodthorn", "Orchid Malevolence", "Scythe of Vyse"],
            countered_by={"heroes": ["Phantom Assassin", "Legion Commander"], "description": "Legion Duel игнорирует BKB"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Shield"],
            early_game=["Power Treads", "Magic Wand", "Ring of Health"],
            mid_game=["Battle Fury", "Manta Style", "Black King Bar"],
            late_game=["Butterfly", "Abyssal Blade", "Satanic"],
            situational=["Monkey King Bar", "Bloodthorn"]
        ),
        stats=HeroStats(win_rate=49.5, pick_rate=12.1, tier="B")
    ),
    
    "spectre": Hero(
        id="spectre",
        name="Spectre",
        localized_name="Spectre",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Durable", "Escape"],
        description="Керри с глобальным присутствием. Ультимейт Haunt разрывает файты.",
        strengths=["Глобальное присутствие", "Отражение урона", "Сильный лейт"],
        weaknesses=["Медленный фарм", "Слаб рано", "Зависит от Radiance"],
        counters=HeroCounters(
            weak_against=["Anti-Mage", "Necrophos", "Viper", "Omniknight"],
            counter_items=["Silver Edge", "Diffusal Blade", "Scythe of Vyse"],
            countered_by={"heroes": ["Anti-Mage", "Necrophos"], "description": "Anti-Mage сжигает ману, Necrophos замедляет"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Shield"],
            early_game=["Power Treads", "Magic Wand", "Urn of Shadows"],
            mid_game=["Radiance", "Manta Style", "Blade Mail"],
            late_game=["Heart of Tarrasque", "Butterfly", "Abyssal Blade", "Refresher Orb"],
            situational=["Silver Edge", "Bloodthorn", "Nullifier"]
        ),
        stats=HeroStats(win_rate=51.2, pick_rate=11.5, tier="A")
    ),
    
    "faceless_void": Hero(
        id="faceless_void",
        name="Faceless Void",
        localized_name="Faceless Void",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Initiator", "Disabler", "Escape"],
        description="Керри с Chronosphere — лучшим станом в игре.",
        strengths=["Chronosphere", "Time Walk для escape", "Бэкдор потенциал"],
        weaknesses=["Сильно зависит от ультимейта", "Слаб без предметов", "Контрится"],
        counters=HeroCounters(
            weak_against=["Axe", "Silencer", "Viper", "Winter Wyvern"],
            counter_items=["Force Staff", "Eul's Scepter", "Ghost Scepter", "Aeon Disk"],
            countered_by={"heroes": ["Axe", "Silencer"], "description": "Axe Call в хроносфере, Silencer ульт"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Circlet"],
            early_game=["Power Treads", "Magic Wand", "Mask of Madness"],
            mid_game=["Battle Fury", "Black King Bar", "Maelstrom"],
            late_game=["Butterfly", "Satanic", "Abyssal Blade", "Refresher Orb"],
            situational=["Silver Edge", "Monkey King Bar", "Bloodthorn"]
        ),
        stats=HeroStats(win_rate=50.8, pick_rate=13.2, tier="A")
    ),
    
    # MID
    "void_spirit": Hero(
        id="void_spirit",
        name="Void Spirit",
        localized_name="Void Spirit",
        primary_attr="int",
        attack_type="Melee",
        roles=["Carry", "Escape", "Nuker", "Disabler"],
        description="Мобильный mid с высоким взрывным уроном.",
        strengths=["Высокая мобильность", "Взрывной магический урон", "Сложно поймать"],
        weaknesses=["Уязвим к silence", "Нужна мана", "Падает в лейте"],
        counters=HeroCounters(
            weak_against=["Silencer", "Doom", "Bloodseeker", "Anti-Mage"],
            counter_items=["Orchid Malevolence", "Bloodthorn", "Scythe of Vyse", "Abyssal Blade"],
            countered_by={"heroes": ["Silencer", "Doom"], "description": "Silence отключает способности"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Circlet", "Branches", "Faerie Fire"],
            early_game=["Bottle", "Power Treads", "Magic Wand", "Kaya"],
            mid_game=["Orchid Malevolence", "Black King Bar", "Sange and Kaya"],
            late_game=["Bloodthorn", "Refresher Orb", "Octarine Core"],
            situational=["Eul's Scepter", "Shiva's Guard", "Scythe of Vyse"]
        ),
        stats=HeroStats(win_rate=50.5, pick_rate=18.3, tier="A")
    ),
    
    "ember_spirit": Hero(
        id="ember_spirit",
        name="Ember Spirit",
        localized_name="Ember Spirit",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Escape", "Nuker", "Disabler", "Initiator"],
        description="Мобильный carry с физическим и магическим уроном.",
        strengths=["Высочайшая мобильность", "Смешанный урон", "Силен на всех стадиях"],
        weaknesses=["Уязвим к silence", "Требует маны", "Сложная механика"],
        counters=HeroCounters(
            weak_against=["Silencer", "Faceless Void", "Storm Spirit", "Void Spirit"],
            counter_items=["Orchid Malevolence", "Bloodthorn", "Scythe of Vyse", "Abyssal Blade"],
            countered_by={"heroes": ["Silencer", "Faceless Void"], "description": "Silencer и Faceless Void контрят мобильность"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Circlet", "Branches", "Faerie Fire"],
            early_game=["Bottle", "Phase Boots", "Magic Wand", "Maelstrom"],
            mid_game=["Black King Bar", "Mjollnir", "Crystalys"],
            late_game=["Daedalus", "Octarine Core", "Refresher Orb", "Boots of Travel"],
            situational=["Radiance", "Linken's Sphere", "Shiva's Guard"]
        ),
        stats=HeroStats(win_rate=51.2, pick_rate=16.7, tier="S")
    ),
    
    "invoker": Hero(
        id="invoker",
        name="Invoker",
        localized_name="Invoker",
        primary_attr="uni",
        attack_type="Ranged",
        roles=["Carry", "Nuker", "Disabler", "Escape", "Pusher"],
        description="Самый сложный герой с 10 способностями.",
        strengths=["Огромный урон", "Много способностей", "Сильный на всех стадиях"],
        weaknesses=["Сложная механика", "Уязвим к ганкам", "Нужна мана"],
        counters=HeroCounters(
            weak_against=["Anti-Mage", "Nyx Assassin", "Silencer", "Pugna"],
            counter_items=["Orchid Malevolence", "Bloodthorn", "Scythe of Vyse", "Black King Bar"],
            countered_by={"heroes": ["Anti-Mage", "Nyx Assassin"], "description": "Anti-Mage сжигает ману, Nyx взрывает ману"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Circlet", "Branches", "Faerie Fire"],
            early_game=["Null Talisman", "Boots of Speed", "Magic Wand"],
            mid_game=["Aghanim's Scepter", "Octarine Core", "Black King Bar"],
            late_game=["Refresher Orb", "Shiva's Guard", "Scythe of Vyse", "Bloodthorn"],
            situational=["Linken's Sphere", "Eul's Scepter", "Blink Dagger"]
        ),
        stats=HeroStats(win_rate=49.8, pick_rate=14.5, tier="A")
    ),
    
    "storm_spirit": Hero(
        id="storm_spirit",
        name="Storm Spirit",
        localized_name="Storm Spirit",
        primary_attr="int",
        attack_type="Ranged",
        roles=["Carry", "Escape", "Nuker", "Initiator", "Disabler"],
        description="Мобильный маг с Ball Lightning.",
        strengths=["Бесконечная мобильность", "Высокий урон", "Соло убийства"],
        weaknesses=["Зависим от Bloodstone", "Уязвим к silence", "Нужна мана"],
        counters=HeroCounters(
            weak_against=["Anti-Mage", "Silencer", "Doom", "Nyx Assassin"],
            counter_items=["Orchid Malevolence", "Bloodthorn", "Scythe of Vyse", "Abyssal Blade"],
            countered_by={"heroes": ["Anti-Mage", "Silencer"], "description": "Silence и мана-бёрн контрят"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Circlet", "Branches", "Faerie Fire"],
            early_game=["Null Talisman", "Boots of Speed", "Magic Wand"],
            mid_game=["Bloodstone", "Black King Bar", "Kaya and Sange"],
            late_game=["Bloodthorn", "Shiva's Guard", "Scythe of Vyse", "Refresher Orb"],
            situational=["Linken's Sphere", "Octarine Core", "Hurricane Pike"]
        ),
        stats=HeroStats(win_rate=48.5, pick_rate=10.2, tier="B")
    ),
    
    # OFFLANE
    "slardar": Hero(
        id="slardar",
        name="Slardar",
        localized_name="Slardar",
        primary_attr="str",
        attack_type="Melee",
        roles=["Carry", "Durable", "Initiator", "Disabler", "Escape"],
        description="Сильный инициатор с минус броней.",
        strengths=["Сильная инициация", "Минус броня", "Высокая мобильность"],
        weaknesses=["Уязвим к kiting'у", "Проблемы против иллюзий", "Требует Blink"],
        counters=HeroCounters(
            weak_against=["Phantom Lancer", "Terrorblade", "Naga Siren", "Tinker"],
            counter_items=["Force Staff", "Ghost Scepter", "Eul's Scepter", "Silver Edge"],
            countered_by={"heroes": ["Phantom Lancer", "Terrorblade"], "description": "Silver Edge брейкает пассивку"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Shield"],
            early_game=["Phase Boots", "Magic Wand", "Blink Dagger"],
            mid_game=["Black King Bar", "Aghanim's Scepter", "Force Staff"],
            late_game=["Assault Cuirass", "Shiva's Guard", "Lotus Orb", "Abyssal Blade"],
            situational=["Lotus Orb", "Heaven's Halberd", "Guardian Greaves"]
        ),
        stats=HeroStats(win_rate=49.8, pick_rate=8.5, tier="B")
    ),
    
    "tidehunter": Hero(
        id="tidehunter",
        name="Tidehunter",
        localized_name="Tidehunter",
        primary_attr="str",
        attack_type="Melee",
        roles=["Initiator", "Durable", "Disabler", "Nuker"],
        description="Мощный танк с лучшим AoE контролем (Ravage).",
        strengths=["Ravage — лучший AoE стан", "Высокая живучесть", "Anchor Smash"],
        weaknesses=["Долгий кд на Ravage", "Уязвим к silence", "Медленный фарм"],
        counters=HeroCounters(
            weak_against=["Silencer", "Enigma", "Rubick", "Doom"],
            counter_items=["Black King Bar", "Linken's Sphere", "Lotus Orb", "Silver Edge"],
            countered_by={"heroes": ["Silencer", "Enigma"], "description": "Silencer ульт, Enigma Black Hole"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Clarity", "Shield"],
            early_game=["Arcane Boots", "Magic Wand", "Blink Dagger"],
            mid_game=["Black King Bar", "Force Staff", "Mekansm"],
            late_game=["Refresher Orb", "Shiva's Guard", "Lotus Orb", "Guardian Greaves"],
            situational=["Pipe of Insight", "Crimson Guard", "Aghanim's Scepter"]
        ),
        stats=HeroStats(win_rate=50.1, pick_rate=10.2, tier="A")
    ),
    
    "axe": Hero(
        id="axe",
        name="Axe",
        localized_name="Axe",
        primary_attr="str",
        attack_type="Melee",
        roles=["Initiator", "Durable", "Disabler", "Jungler"],
        description="Инициатор с Berserker's Call и Culling Blade.",
        strengths=["Мощный дизейбл", "True damage ульт", "Быстрый фарм леса"],
        weaknesses=["Уязвим к магии", "Зависит от Blink", "Контрится"],
        counters=HeroCounters(
            weak_against=["Viper", "Venomancer", "Necrophos", "Pugna"],
            counter_items=["Force Staff", "Ghost Scepter", "Eul's Scepter", "Glimmer Cape"],
            countered_by={"heroes": ["Viper", "Venomancer"], "description": "Магический урон и замедление"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Stout Shield", "Iron Branch"],
            early_game=["Tranquil Boots", "Magic Wand", "Blink Dagger"],
            mid_game=["Black King Bar", "Blade Mail", "Force Staff"],
            late_game=["Heart of Tarrasque", "Lotus Orb", "Aghanim's Scepter", "Shiva's Guard"],
            situational=["Crimson Guard", "Pipe of Insight", "Heaven's Halberd"]
        ),
        stats=HeroStats(win_rate=51.5, pick_rate=12.8, tier="A")
    ),
    
    "mars": Hero(
        id="mars",
        name="Mars",
        localized_name="Mars",
        primary_attr="str",
        attack_type="Melee",
        roles=["Carry", "Initiator", "Disabler", "Durable"],
        description="Инициатор с Arena of Blood.",
        strengths=["Сильный контроль", "Блокирование атак", "Высокий урон"],
        weaknesses=["Уязвим к магии", "Зависит от ультимейта", "Мана-зависимый"],
        counters=HeroCounters(
            weak_against=["Viper", "Venomancer", "Lifestealer", "Riki"],
            counter_items=["Force Staff", "Blink Dagger", "Eul's Scepter", "Black King Bar"],
            countered_by={"heroes": ["Viper", "Lifestealer"], "description": "Rage игнорирует стан, Viper замедляет"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Circlet"],
            early_game=["Phase Boots", "Magic Wand", "Blink Dagger"],
            mid_game=["Black King Bar", "Desolator", "Aghanim's Scepter"],
            late_game=["Satanic", "Assault Cuirass", "Daedalus", "Refresher Orb"],
            situational=["Silver Edge", "Bloodthorn", "Heaven's Halberd"]
        ),
        stats=HeroStats(win_rate=50.2, pick_rate=11.3, tier="A")
    ),
    
    "doom": Hero(
        id="doom",
        name="Doom",
        localized_name="Doom",
        primary_attr="str",
        attack_type="Melee",
        roles=["Carry", "Disabler", "Initiator", "Durable", "Nuker"],
        description="Оффлейнер с Doom — сильнейшим silence в игре.",
        strengths=["Doom отключает героя", "Быстрый фарм", "Танк"],
        weaknesses=["Медленный", "Зависим от фарма", "Контрится Linken's"],
        counters=HeroCounters(
            weak_against=["Lifestealer", "Weaver", "Phantom Lancer", "Anti-Mage"],
            counter_items=["Linken's Sphere", "Lotus Orb", "Black King Bar", "Aghanim's Scepter"],
            countered_by={"heroes": ["Lifestealer", "Weaver"], "description": "Rage и Time Lapse снимают Doom"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Shield"],
            early_game=["Phase Boots", "Magic Wand", "Hand of Midas"],
            mid_game=["Black King Bar", "Shiva's Guard", "Aghanim's Scepter"],
            late_game=["Refresher Orb", "Octarine Core", "Assault Cuirass", "Bloodthorn"],
            situational=["Silver Edge", "Heaven's Halberd", "Lotus Orb"]
        ),
        stats=HeroStats(win_rate=49.2, pick_rate=8.7, tier="B")
    ),
    
    # SUPPORTS
    "shadow_shaman": Hero(
        id="shadow_shaman",
        name="Shadow Shaman",
        localized_name="Shadow Shaman",
        primary_attr="int",
        attack_type="Ranged",
        roles=["Support", "Pusher", "Disabler", "Nuker", "Initiator"],
        description="Сильнейший пушер с длиннейшим станом.",
        strengths=["Длинный стан", "Мощный пуш", "Hex для дизейбла"],
        weaknesses=["Очень хрупкий", "Медленный", "Легко убивается"],
        counters=HeroCounters(
            weak_against=["Pudge", "Clockwerk", "Spirit Breaker", "Night Stalker"],
            counter_items=["Force Staff", "Glimmer Cape", "Ghost Scepter", "Black King Bar"],
            countered_by={"heroes": ["Pudge", "Clockwerk"], "description": "Гэпклоуэры убивают"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Clarity", "Observer Ward", "Sentry Ward"],
            early_game=["Arcane Boots", "Magic Wand", "Wind Lace"],
            mid_game=["Aether Lens", "Glimmer Cape", "Aghanim's Scepter"],
            late_game=["Refresher Orb", "Octarine Core", "Force Staff", "Ghost Scepter"],
            situational=["Blink Dagger", "Aeon Disk", "Ghost Scepter"]
        ),
        stats=HeroStats(win_rate=48.5, pick_rate=14.3, tier="B")
    ),
    
    "lich": Hero(
        id="lich",
        name="Lich",
        localized_name="Lich",
        primary_attr="int",
        attack_type="Ranged",
        roles=["Support", "Nuker", "Disabler"],
        description="Support с Chain Frost — разрывом в файтах.",
        strengths=["Chain Frost", "Ice Armor", "Sacrifice для контроля линии"],
        weaknesses=["Хрупкий", "Мана зависимость", "Уязвим к мана-бёрну"],
        counters=HeroCounters(
            weak_against=["Anti-Mage", "Nyx Assassin", "Pugna", "Morphling"],
            counter_items=["Black King Bar", "Glimmer Cape", "Force Staff", "Lotus Orb"],
            countered_by={"heroes": ["Anti-Mage", "Nyx Assassin"], "description": "Anti-Mage сжигает ману"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Mango", "Observer Ward"],
            early_game=["Tranquil Boots", "Magic Wand", "Wind Lace"],
            mid_game=["Glimmer Cape", "Force Staff", "Aghanim's Scepter"],
            late_game=["Octarine Core", "Refresher Orb", "Ghost Scepter", "Lotus Orb"],
            situational=["Aether Lens", "Ghost Scepter", "Solar Crest"]
        ),
        stats=HeroStats(win_rate=51.5, pick_rate=11.8, tier="A")
    ),
    
    "lion": Hero(
        id="lion",
        name="Lion",
        localized_name="Lion",
        primary_attr="int",
        attack_type="Ranged",
        roles=["Support", "Disabler", "Nuker", "Initiator"],
        description="Дизейблер с двумя станами и Finger of Death.",
        strengths=["Два disables", "Finger of Death", "Mana Drain", "Сильный в ганках"],
        weaknesses=["Очень хрупкий", "Медленный", "Зависим от позиционирования"],
        counters=HeroCounters(
            weak_against=["Nyx Assassin", "Pudge", "Clockwerk", "Lifestealer"],
            counter_items=["Force Staff", "Glimmer Cape", "Black King Bar", "Lotus Orb"],
            countered_by={"heroes": ["Nyx Assassin", "Pudge"], "description": "Nyx отражает Finger"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Clarity", "Observer Ward"],
            early_game=["Tranquil Boots", "Magic Wand", "Wind Lace"],
            mid_game=["Blink Dagger", "Aether Lens", "Force Staff"],
            late_game=["Aghanim's Scepter", "Octarine Core", "Refresher Orb", "Glimmer Cape"],
            situational=["Aeon Disk", "Ghost Scepter", "Lotus Orb"]
        ),
        stats=HeroStats(win_rate=47.8, pick_rate=13.5, tier="B")
    ),
    
    "pudge": Hero(
        id="pudge",
        name="Pudge",
        localized_name="Pudge",
        primary_attr="str",
        attack_type="Melee",
        roles=["Disabler", "Initiator", "Durable", "Nuker"],
        description="Гэпклоуэр с Meat Hook.",
        strengths=["Meat Hook", "Dismember", "Высокое HP", "Фановый герой"],
        weaknesses=["Зависит от хука", "Медленный", "Фидит если промахивается"],
        counters=HeroCounters(
            weak_against=["Vengeful Spirit", "Chen", "Kunkka", "Lifestealer"],
            counter_items=["Force Staff", "Glimmer Cape", "Black King Bar", "Lotus Orb"],
            countered_by={"heroes": ["Vengeful Spirit", "Lifestealer"], "description": "Rage игнорирует ульт, Venge свопает"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Gauntlets of Strength", "Iron Branch"],
            early_game=["Tranquil Boots", "Magic Wand", "Soul Ring"],
            mid_game=["Blink Dagger", "Black King Bar", "Aghanim's Scepter"],
            late_game=["Heart of Tarrasque", "Lotus Orb", "Shiva's Guard", "Force Staff"],
            situational=["Pipe of Insight", "Crimson Guard", "Heaven's Halberd"]
        ),
        stats=HeroStats(win_rate=52.8, pick_rate=22.5, tier="S")
    ),
    
    "crystal_maiden": Hero(
        id="crystal_maiden",
        name="Crystal Maiden",
        localized_name="Crystal Maiden",
        primary_attr="int",
        attack_type="Ranged",
        roles=["Support", "Disabler", "Nuker", "Jungler"],
        description="Support с Arcane Aura для команды.",
        strengths=["Arcane Aura — реген маны", "Freezing Field", "Сильный ранний гейм"],
        weaknesses=["Очень медленная", "Хрупкая", "Легкая цель"],
        counters=HeroCounters(
            weak_against=["Bounty Hunter", "Riki", "Spirit Breaker", "Nyx Assassin"],
            counter_items=["Force Staff", "Glimmer Cape", "Ghost Scepter", "Black King Bar"],
            countered_by={"heroes": ["Bounty Hunter", "Riki"], "description": "Инвиз герои убивают легко"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Clarity", "Observer Ward"],
            early_game=["Arcane Boots", "Magic Wand", "Wind Lace"],
            mid_game=["Glimmer Cape", "Force Staff", "Aghanim's Scepter"],
            late_game=["Black King Bar", "Ghost Scepter", "Aether Lens", "Lotus Orb"],
            situational=["Blink Dagger", "Aeon Disk", "Eul's Scepter"]
        ),
        stats=HeroStats(win_rate=48.2, pick_rate=9.8, tier="C")
    ),
    
    "rubick": Hero(
        id="rubick",
        name="Rubick",
        localized_name="Rubick",
        primary_attr="int",
        attack_type="Ranged",
        roles=["Support", "Disabler", "Nuker"],
        description="Support с Spell Steal — ворует способности.",
        strengths=["Spell Steal", "Телекинезис", "Сильный против магов"],
        weaknesses=["Хрупкий", "Зависит от вражеских способностей", "Сложный"],
        counters=HeroCounters(
            weak_against=["Silencer", "Nyx Assassin", "Bounty Hunter", "Riki"],
            counter_items=["Force Staff", "Glimmer Cape", "Ghost Scepter", "Black King Bar"],
            countered_by={"heroes": ["Silencer", "Nyx Assassin"], "description": "Silencer ульт, Nyx мана-бёрн"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Mango", "Observer Ward"],
            early_game=["Arcane Boots", "Magic Wand", "Wind Lace"],
            mid_game=["Blink Dagger", "Aether Lens", "Force Staff"],
            late_game=["Aghanim's Scepter", "Octarine Core", "Refresher Orb", "Glimmer Cape"],
            situational=["Black King Bar", "Ghost Scepter", "Lotus Orb"]
        ),
        stats=HeroStats(win_rate=49.5, pick_rate=8.2, tier="B")
    ),
    
    # HARD CARRY
    "terrorblade": Hero(
        id="terrorblade",
        name="Terrorblade",
        localized_name="Terrorblade",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Pusher", "Nuker"],
        description="Керри с Metamorphosis и иллюзиями.",
        strengths=["Высокий урон", "Иллюзии", "Сильный пуш", "Reflection"],
        weaknesses=["Слаб рано", "Зависит от Metamorphosis", "Контрится AoE"],
        counters=HeroCounters(
            weak_against=["Axe", "Earthshaker", "Sven", "Naga Siren"],
            counter_items=["Battle Fury", "Mjollnir", "Radiance", "Shiva's Guard"],
            countered_by={"heroes": ["Axe", "Earthshaker"], "description": "Axe Call, Earthshaker Echo Slam"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Circlet"],
            early_game=["Power Treads", "Magic Wand", "Wraith Band"],
            mid_game=["Dragon Lance", "Black King Bar", "Manta Style"],
            late_game=["Satanic", "Butterfly", "Skadi", "Bloodthorn"],
            situational=["Silver Edge", "Hurricane Pike", "Monkey King Bar"]
        ),
        stats=HeroStats(win_rate=50.5, pick_rate=10.8, tier="A")
    ),
    
    "medusa": Hero(
        id="medusa",
        name="Medusa",
        localized_name="Medusa",
        primary_attr="agi",
        attack_type="Ranged",
        roles=["Carry", "Durable", "Disabler"],
        description="Супер-лейт керри с Mana Shield.",
        strengths=["Невероятный лейт", "Mana Shield", "Split Shot", "Stone Gaze"],
        weaknesses=["Медленный фарм", "Слаб рано", "Зависит от предметов"],
        counters=HeroCounters(
            weak_against=["Anti-Mage", "Nyx Assassin", "Invoker", "Silencer"],
            counter_items=["Diffusal Blade", "Necronomicon", "Mana Void", "Orchid Malevolence"],
            countered_by={"heroes": ["Anti-Mage", "Nyx Assassin"], "description": "Мана-бёрн убивает"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Circlet", "Branches"],
            early_game=["Power Treads", "Magic Wand", "Wraith Band"],
            mid_game=["Linken's Sphere", "Manta Style", "Skadi"],
            late_game=["Butterfly", "Satanic", "Bloodthorn", "Refresher Orb"],
            situational=["Silver Edge", "Monkey King Bar", "Hurricane Pike"]
        ),
        stats=HeroStats(win_rate=51.8, pick_rate=9.5, tier="A")
    ),
    
    "juggernaut": Hero(
        id="juggernaut",
        name="Juggernaut",
        localized_name="Juggernaut",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Pusher", "Escape"],
        description="Универсальный керри с Blade Fury и Omnislash.",
        strengths=["Универсальный", "Быстрый фарм", "Healing Ward", "Omnislash"],
        weaknesses=["Уязвим к контролю", "Omnislash контрится", "Средний лейт"],
        counters=HeroCounters(
            weak_against=["Axe", "Lion", "Shadow Shaman", "Ursa"],
            counter_items=["Ghost Scepter", "Force Staff", "Eul's Scepter", "Heaven's Halberd"],
            countered_by={"heroes": ["Axe", "Lion"], "description": "Axe Call, Lion Hex + Finger"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Circlet"],
            early_game=["Phase Boots", "Magic Wand", "Wraith Band"],
            mid_game=["Battle Fury", "Black King Bar", "Manta Style"],
            late_game=["Satanic", "Butterfly", "Abyssal Blade", "Bloodthorn"],
            situational=["Silver Edge", "Monkey King Bar", "Skadi"]
        ),
        stats=HeroStats(win_rate=50.2, pick_rate=14.8, tier="A")
    ),
    
    "sven": Hero(
        id="sven",
        name="Sven",
        localized_name="Sven",
        primary_attr="str",
        attack_type="Melee",
        roles=["Carry", "Disabler", "Initiator", "Pusher"],
        description="Керри с God's Strength и клеевом уроном.",
        strengths=["Огромный урон", "God's Strength", "Storm Hammer", "Быстрый фарм"],
        weaknesses=["Медленный", "Зависим от ультимейта", "Кайтится"],
        counters=HeroCounters(
            weak_against=["Viper", "Venomancer", "Drow Ranger", "Phantom Lancer"],
            counter_items=["Force Staff", "Ghost Scepter", "Heaven's Halberd", "Eul's Scepter"],
            countered_by={"heroes": ["Viper", "Phantom Lancer"], "description": "Замедление и иллюзии"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Circlet"],
            early_game=["Power Treads", "Magic Wand", "Mask of Madness"],
            mid_game=["Black King Bar", "Daedalus", "Sange and Yasha"],
            late_game=["Satanic", "Butterfly", "Abyssal Blade", "Bloodthorn"],
            situational=["Silver Edge", "Monkey King Bar", "Swift Blink"]
        ),
        stats=HeroStats(win_rate=49.8, pick_rate=11.2, tier="B")
    ),
    
    "morphling": Hero(
        id="morphling",
        name="Morphling",
        localized_name="Morphling",
        primary_attr="agi",
        attack_type="Ranged",
        roles=["Carry", "Escape", "Nuker", "Disabler"],
        description="Гибкий керри с Waveform и Morph.",
        strengths=["Высокая мобильность", "Гибкость билдов", "Waveform", "Replicate"],
        weaknesses=["Сложный", "Зависим от маны", "Уязвим к мана-бёрну"],
        counters=HeroCounters(
            weak_against=["Anti-Mage", "Nyx Assassin", "Invoker", "Silencer"],
            counter_items=["Diffusal Blade", "Orchid Malevolence", "Scythe of Vyse"],
            countered_by={"heroes": ["Anti-Mage", "Nyx Assassin"], "description": "Мана-бёрн убивает"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Circlet", "Branches"],
            early_game=["Power Treads", "Magic Wand", "Wraith Band"],
            mid_game=["Black King Bar", "Linken's Sphere", "Manta Style"],
            late_game=["Satanic", "Butterfly", "Skadi", "Bloodthorn"],
            situational=["Silver Edge", "Monkey King Bar", "Ethereal Blade"]
        ),
        stats=HeroStats(win_rate=48.5, pick_rate=7.8, tier="B")
    ),
    
    "gyrocopter": Hero(
        id="gyrocopter",
        name="Gyrocopter",
        localized_name="Gyrocopter",
        primary_attr="agi",
        attack_type="Ranged",
        roles=["Carry", "Nuker", "Disabler"],
        description="Керри с Flak Cannon — AoE уроном.",
        strengths=["Высокий AoE урон", "Flak Cannon", "Call Down", "Сильный в файтах"],
        weaknesses=["Медленный", "Низкая дальность", "Зависим от предметов"],
        counters=HeroCounters(
            weak_against=["Phantom Assassin", "Storm Spirit", "Anti-Mage", "Nyx Assassin"],
            counter_items=["Blade Mail", "Heaven's Halberd", "Ghost Scepter", "Force Staff"],
            countered_by={"heroes": ["Phantom Assassin", "Storm Spirit"], "description": "Блинкеры убивают быстро"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Circlet", "Branches"],
            early_game=["Power Treads", "Magic Wand", "Wraith Band"],
            mid_game=["Black King Bar", "Sange and Yasha", "Daedalus"],
            late_game=["Satanic", "Butterfly", "Bloodthorn", "Swift Blink"],
            situational=["Silver Edge", "Monkey King Bar", "Hurricane Pike"]
        ),
        stats=HeroStats(win_rate=50.5, pick_rate=8.9, tier="B")
    ),
    
    "luna": Hero(
        id="luna",
        name="Luna",
        localized_name="Luna",
        primary_attr="agi",
        attack_type="Ranged",
        roles=["Carry", "Nuker", "Pusher"],
        description="Быстрый керри с Moon Glaives и Eclipse.",
        strengths=["Быстрый фарм", "Высокий урон", "Eclipse", "Лунный блеск"],
        weaknesses=["Хрупкая", "Короткая дальность", "Зависит от позиционирования"],
        counters=HeroCounters(
            weak_against=["Phantom Assassin", "Storm Spirit", "Anti-Mage", "Nyx Assassin"],
            counter_items=["Blade Mail", "Heaven's Halberd", "Ghost Scepter", "Force Staff"],
            countered_by={"heroes": ["Phantom Assassin", "Storm Spirit"], "description": "Блинкеры убивают быстро"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Circlet", "Branches"],
            early_game=["Power Treads", "Magic Wand", "Wraith Band"],
            mid_game=["Black King Bar", "Manta Style", "Dragon Lance"],
            late_game=["Satanic", "Butterfly", "Skadi", "Bloodthorn"],
            situational=["Silver Edge", "Monkey King Bar", "Hurricane Pike"]
        ),
        stats=HeroStats(win_rate=51.2, pick_rate=10.5, tier="A")
    ),
    
    "razor": Hero(
        id="razor",
        name="Razor",
        localized_name="Razor",
        primary_attr="agi",
        attack_type="Ranged",
        roles=["Carry", "Durable", "Nuker"],
        description="Танкующий керри с Static Link.",
        strengths=["Static Link крадет урон", "Высокая живучесть", "Eye of the Storm"],
        weaknesses=["Медленный", "Низкий урон без Link", "Кайтится"],
        counters=HeroCounters(
            weak_against=["Sniper", "Drow Ranger", "Viper", "Venomancer"],
            counter_items=["Force Staff", "Ghost Scepter", "Heaven's Halberd", "Eul's Scepter"],
            countered_by={"heroes": ["Sniper", "Drow Ranger"], "description": "Дальнобойные кайтят"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Circlet", "Branches"],
            early_game=["Phase Boots", "Magic Wand", "Wraith Band"],
            mid_game=["Black King Bar", "Sange and Yasha", "Aghanim's Scepter"],
            late_game=["Satanic", "Butterfly", "Skadi", "Refresher Orb"],
            situational=["Silver Edge", "Bloodthorn", "Hurricane Pike"]
        ),
        stats=HeroStats(win_rate=49.2, pick_rate=6.8, tier="C")
    ),
    
    "viper": Hero(
        id="viper",
        name="Viper",
        localized_name="Viper",
        primary_attr="agi",
        attack_type="Ranged",
        roles=["Carry", "Durable", "Disabler", "Nuker"],
        description="Токсичный керри с Corrosive Skin.",
        strengths=["Сильный на линии", "Замедление", "Танк", "Простой"],
        weaknesses=["Медленный", "Нет мобильности", "Падает в лейте"],
        counters=HeroCounters(
            weak_against=["Sniper", "Drow Ranger", "Storm Spirit", "Anti-Mage"],
            counter_items=["Black King Bar", "Force Staff", "Heaven's Halberd", "Eul's Scepter"],
            countered_by={"heroes": ["Sniper", "Storm Spirit"], "description": "Мобильные герои убивают"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Circlet", "Branches"],
            early_game=["Phase Boots", "Magic Wand", "Wraith Band"],
            mid_game=["Black King Bar", "Dragon Lance", "Aghanim's Scepter"],
            late_game=["Satanic", "Butterfly", "Skadi", "Bloodthorn"],
            situational=["Silver Edge", "Hurricane Pike", "Monkey King Bar"]
        ),
        stats=HeroStats(win_rate=51.8, pick_rate=8.2, tier="B")
    ),
    
    "weaver": Hero(
        id="weaver",
        name="Weaver",
        localized_name="Weaver",
        primary_attr="agi",
        attack_type="Ranged",
        roles=["Carry", "Escape"],
        description="Мобильный керри с Shukuchi и Time Lapse.",
        strengths=["Высокая мобильность", "Time Lapse", "Трудно убить", "Geminate Attack"],
        weaknesses=["Хрупкий", "Зависим от маны", "Контрится Detection"],
        counters=HeroCounters(
            weak_against=["Slardar", "Bounty Hunter", "Spirit Breaker", "Axe"],
            counter_items=["Dust of Appearance", "Sentry Ward", "Gem of True Sight", "Silver Edge"],
            countered_by={"heroes": ["Slardar", "Bounty Hunter"], "description": "True Sight убивает инвиз"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Circlet", "Branches"],
            early_game=["Power Treads", "Magic Wand", "Wraith Band"],
            mid_game=["Linken's Sphere", "Black King Bar", "Dragon Lance"],
            late_game=["Satanic", "Butterfly", "Bloodthorn", "Swift Blink"],
            situational=["Silver Edge", "Monkey King Bar", "Hurricane Pike"]
        ),
        stats=HeroStats(win_rate=50.5, pick_rate=7.5, tier="B")
    ),
    
    "ursa": Hero(
        id="ursa",
        name="Ursa",
        localized_name="Ursa",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Durable", "Disabler", "Jungler"],
        description="Берсерк с Fury Swipes.",
        strengths=["Огромный урон", "Fury Swipes", "Enrage", "Быстрый Рошан"],
        weaknesses=["Медленный", "Нет мобильности", "Кайтится"],
        counters=HeroCounters(
            weak_against=["Viper", "Venomancer", "Drow Ranger", "Phantom Lancer"],
            counter_items=["Force Staff", "Ghost Scepter", "Heaven's Halberd", "Eul's Scepter"],
            countered_by={"heroes": ["Viper", "Phantom Lancer"], "description": "Замедление и иллюзии"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Stout Shield", "Iron Branch"],
            early_game=["Phase Boots", "Magic Wand", "Morbid Mask"],
            mid_game=["Black King Bar", "Sange and Yasha", "Basher"],
            late_game=["Satanic", "Butterfly", "Abyssal Blade", "Swift Blink"],
            situational=["Silver Edge", "Bloodthorn", "Skadi"]
        ),
        stats=HeroStats(win_rate=51.2, pick_rate=9.8, tier="A")
    ),
    
    "bloodseeker": Hero(
        id="bloodseeker",
        name="Bloodseeker",
        localized_name="Bloodseeker",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Disabler", "Jungler", "Nuker"],
        description="Керри с Rupture и Thirst.",
        strengths=["Высокая скорость", "Rupture", "Thirst", "Быстрый фарм"],
        weaknesses=["Хрупкий", "Зависит от ультимейта", "Контрится TP"],
        counters=HeroCounters(
            weak_against=["Phantom Assassin", "Anti-Mage", "Storm Spirit", "Nyx Assassin"],
            counter_items=["Town Portal Scroll", "Force Staff", "Ghost Scepter", "Glimmer Cape"],
            countered_by={"heroes": ["Phantom Assassin", "Anti-Mage"], "description": "Блинкеры убивают"}
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Salve", "Quelling Blade", "Circlet"],
            early_game=["Power Treads", "Magic Wand", "Wraith Band"],
            mid_game=["Black King Bar", "Sange and Yasha", "Maelstrom"],
            late_game=["Satanic", "Butterfly", "Bloodthorn", "Swift Blink"],
            situational=["Silver Edge", "Monkey King Bar", "Skadi"]
        ),
        stats=HeroStats(win_rate=48.5, pick_rate=6.2, tier="C")
    ),
}

HEROES_BY_NAME = {}
for hero_id, hero in HEROES_DATABASE.items():
    HEROES_BY_NAME[hero_id] = hero
    HEROES_BY_NAME[hero.name.lower()] = hero
    HEROES_BY_NAME[hero.name.lower().replace(" ", "")] = hero
    if hero.localized_name:
        HEROES_BY_NAME[hero.localized_name.lower()] = hero

# ==================== СЕРВИСЫ ====================

class HeroService:
    @staticmethod
    def find_hero(query: str) -> Optional[Hero]:
        query = query.lower().strip().replace(" ", "_").replace("-", "_").replace(" ", "")
        return HEROES_BY_NAME.get(query)
    
    @staticmethod
    def search_heroes(query: str, limit: int = 5) -> List[Hero]:
        query = query.lower()
        matches = []
        
        for hero in HEROES_DATABASE.values():
            search_terms = [
                hero.id,
                hero.name.lower(),
                hero.name.lower().replace(" ", ""),
                hero.localized_name.lower() if hero.localized_name else "",
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
        
        for strength in hero.strengths[:3]:
            lines.append(f"  • {strength}")
            
        lines.extend(["", "❌ *Слабости:*"])
        for weakness in hero.weaknesses[:3]:
            lines.append(f"  • {weakness}")
            
        if hero.stats:
            tier_emoji = {"S": "🔴", "A": "🟠", "B": "🟡", "C": "🟢", "D": "⚪"}.get(hero.stats.tier, "❓")
            lines.extend([
                "",
                f"{tier_emoji} *Тир {hero.stats.tier}* | Винрейт: {hero.stats.win_rate}% | Пик: {hero.stats.pick_rate}%"
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
        
        for i, counter in enumerate(hero.counters.countered_by.get('heroes', [])[:5], 1):
            lines.append(f"{i}. {counter}")
            
        lines.extend(["", "🎒 *Контр-предметы:*"])
        for item in hero.counters.counter_items[:5]:
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
            f"  {' → '.join(build.early_game[:3])}",
            "",
            "🔥 *Мид:*",
            f"  {' → '.join(build.mid_game[:3])}",
            "",
            "👑 *Лейт:*",
            f"  {' → '.join(build.late_game[:3])}",
        ]
        
        if build.situational:
            lines.extend(["", "🔄 *Ситуативно:*", f"  {', '.join(build.situational[:3])}"])
            
        return "\n".join(lines)

# ==================== ML ПРЕДИКТОР ====================

class MatchPredictor:
    """ML-предиктор на основе синергий и контрпиков"""
    
    # Синергии между героями (бонус к силе команды)
    SYNERGIES = {
        # Carry + Support
        ("phantom_lancer", "magnus"): 15,
        ("sven", "magnus"): 15,
        ("melee_carry", "magnus"): 10,
        ("melee_carry", "dark_seer"): 10,
        
        # Mid + Support
        ("storm_spirit", "crystal_maiden"): 12,
        ("invoker", "crystal_maiden"): 10,
        ("mana_hungry", "crystal_maiden"): 8,
        
        # Offlane + Support
        ("slardar", "dazzle"): 12,
        ("axe", "dazzle"): 10,
        
        # Teamfight комбо
        ("enigma", "magnus"): 15,
        ("faceless_void", "magnus"): 12,
        ("tidehunter", "enigma"): 10,
        
        # Пуш
        ("shadow_shaman", "luna"): 10,
        ("shadow_shaman", "terrorblade"): 10,
        
        # Хил + Танк
        ("omniknight", "melee_core"): 8,
        ("dazzle", "axe"): 10,
    }
    
    # Антисинергии (штраф)
    ANTISYNERGIES = {
        ("anti_mage", "medusa"): -10,  # Оба нуждаются в фарме
        ("invoker", "meepo"): -8,      # Сложная механика
        ("techies", "fast_game"): -15, # Затягивает игру
    }
    
    async def predict(self, radiant: List[str], dire: List[str]) -> MatchPrediction:
        """Главный метод предсказания"""
        
        # Анализируем обе команды
        rad_analysis = self._analyze_team(radiant, "Radiant")
        dire_analysis = self._analyze_team(dire, "Dire")
        
        # Находим контрматчапы
        counter_matchups = self._find_counter_matchups(radiant, dire)
        
        # Рассчитываем вероятности
        rad_prob, dire_prob = self._calculate_win_probability(
            rad_analysis, dire_analysis, counter_matchups
        )
        
        # Определяем результат
        result, confidence = self._determine_result(rad_prob, dire_prob)
        
        # Извлекаем ключевые факторы
        key_factors = self._extract_key_factors(
            rad_analysis, dire_analysis, rad_prob, dire_prob, counter_matchups
        )
        
        # Риски
        risk_factors = self._extract_risks(radiant, dire, rad_analysis, dire_analysis)
        
        return MatchPrediction(
            radiant=rad_analysis,
            dire=dire_analysis,
            result=result,
            confidence=confidence,
            win_probability_radiant=rad_prob,
            win_probability_dire=dire_prob,
            key_factors=key_factors,
            risk_factors=risk_factors,
            counter_matchups=counter_matchups
        )
    
    def _analyze_team(self, heroes: List[str], team_name: str) -> TeamAnalysis:
        """Анализ одной команды"""
        
        # Базовые метрики
        synergy = self._calculate_synergy(heroes)
        draft = self._evaluate_draft(heroes)
        meta = self._calculate_meta_score(heroes)
        
        # Анализ сильных/слабых сторон
        strengths, weaknesses = self._analyze_strengths_weaknesses(heroes)
        
        # Ключевые герои
        key_heroes = self._identify_key_heroes(heroes)
        
        # Предварительная вероятность победы
        win_prob = (synergy * 0.4 + draft * 0.3 + meta * 0.3)
        
        return TeamAnalysis(
            team_name=team_name,
            heroes=heroes,
            synergy_score=synergy,
            draft_score=draft,
            meta_score=meta,
            win_probability=win_prob,
            strengths=strengths,
            weaknesses=weaknesses,
            key_heroes=key_heroes
        )
    
    def _calculate_synergy(self, heroes: List[str]) -> float:
        """Расчет синергии команды (0-100)"""
        if len(heroes) < 2:
            return 50.0
        
        score = 50.0  # Базовое значение
        hero_ids = [h.lower().replace(" ", "_") for h in heroes]
        
        # Проверяем синергии
        for (h1, h2), bonus in self.SYNERGIES.items():
            # Прямой порядок
            if self._check_hero_match(h1, hero_ids) and self._check_hero_match(h2, hero_ids):
                score += bonus
            # Обратный порядок
            elif self._check_hero_match(h2, hero_ids) and self._check_hero_match(h1, hero_ids):
                score += bonus
        
        # Проверяем антисинергии
        for (h1, h2), penalty in self.ANTISYNERGIES.items():
            if self._check_hero_match(h1, hero_ids) and self._check_hero_match(h2, hero_ids):
                score += penalty
        
        # Бонус за сбалансированный состав
        roles = self._count_roles(heroes)
        if roles.get("carry", 0) >= 1 and roles.get("support", 0) >= 1:
            score += 10
        if roles.get("initiator", 0) >= 1:
            score += 5
        
        # Штраф за отсутствие керри
        if roles.get("carry", 0) == 0:
            score -= 20
        
        return max(0, min(100, score))
    
    def _check_hero_match(self, pattern: str, hero_ids: List[str]) -> bool:
        """Проверяет соответствие героя паттерну"""
        pattern = pattern.lower()
        
        for hero_id in hero_ids:
            # Точное совпадение
            if hero_id == pattern:
                return True
            # Проверка ролей (melee_carry, mana_hungry и т.д.)
            hero = HeroService.find_hero(hero_id)
            if not hero:
                continue
            
            # Проверка атрибутов
            if pattern == "melee_carry" and hero.attack_type == "Melee" and "Carry" in hero.roles:
                return True
            if pattern == "mana_hungry" and hero.primary_attr == "int":
                return True
            if pattern == "fast_game" and "Pusher" in hero.roles:
                return True
        
        return False
    
    def _count_roles(self, heroes: List[str]) -> Dict[str, int]:
        """Подсчет ролей в команде"""
        roles = {"carry": 0, "support": 0, "initiator": 0, "mid": 0, "offlane": 0}
        
        for h in heroes:
            hero = HeroService.find_hero(h)
            if not hero:
                continue
            
            hero_roles = [r.lower() for r in hero.roles]
            
            if any(r in hero_roles for r in ["carry", "nuker"]):
                roles["carry"] += 1
            if any(r in hero_roles for r in ["support", "healer", "disabler"]):
                roles["support"] += 1
            if any(r in hero_roles for r in ["initiator"]):
                roles["initiator"] += 1
        
        return roles
    
    def _evaluate_draft(self, heroes: List[str]) -> float:
        """Оценка качества драфта (0-100)"""
        score = 50.0
        
        if len(heroes) < 2:
            return score
        
        # Проверяем баланс
        has_carry = False
        has_support = False
        has_initiator = False
        melee_count = 0
        ranged_count = 0
        
        for h in heroes:
            hero = HeroService.find_hero(h)
            if not hero:
                continue
            
            roles = [r.lower() for r in hero.roles]
            
            if any(r in roles for r in ["carry", "nuker"]):
                has_carry = True
            if any(r in roles for r in ["support", "healer"]):
                has_support = True
            if any(r in roles for r in ["initiator", "disabler"]):
                has_initiator = True
            
            if hero.attack_type == "Melee":
                melee_count += 1
            else:
                ranged_count += 1
        
        # Бонусы
        if has_carry:
            score += 15
        if has_support:
            score += 10
        if has_initiator:
            score += 10
        if melee_count > 0 and ranged_count > 0:
            score += 10  # Разнообразие
        
        # Штрафы
        if not has_carry:
            score -= 20
        if len(heroes) < 5:
            score -= (5 - len(heroes)) * 10
        
        return max(0, min(100, score))
    
    def _calculate_meta_score(self, heroes: List[str]) -> float:
        """Оценка соответствия мете (0-100)"""
        if not heroes:
            return 0
        
        total = 0
        for h in heroes:
            hero = HeroService.find_hero(h)
            if hero and hero.stats:
                tier_score = {"S": 100, "A": 85, "B": 70, "C": 55, "D": 40}.get(hero.stats.tier, 50)
                total += tier_score
            else:
                total += 50  # Среднее по умолчанию
        
        return total / len(heroes)
    
    def _analyze_strengths_weaknesses(self, heroes: List[str]) -> Tuple[List[str], List[str]]:
        """Анализ сильных и слабых сторон"""
        strengths = []
        weaknesses = []
        
        roles = self._count_roles(heroes)
        
        # Сильные стороны
        if roles.get("carry", 0) >= 1:
            strengths.append("✅ Есть керри для лейта")
        if roles.get("support", 0) >= 1:
            strengths.append("✅ Есть поддержка")
        if roles.get("initiator", 0) >= 1:
            strengths.append("✅ Есть инициатор")
        
        # Слабые стороны
        if roles.get("carry", 0) == 0:
            weaknesses.append("❌ Нет явного керри")
        if roles.get("support", 0) == 0:
            weaknesses.append("❌ Нет поддержки")
        if roles.get("initiator", 0) == 0:
            weaknesses.append("⚠️ Нет инициатора")
        
        return strengths, weaknesses
    
    def _identify_key_heroes(self, heroes: List[str]) -> List[str]:
        """Определение ключевых героев"""
        key = []
        
        for h in heroes:
            hero = HeroService.find_hero(h)
            if not hero:
                continue
            
            roles = hero.roles
            
            if "Carry" in roles:
                key.append(f"{hero.name} (Керри)")
            elif "Initiator" in roles:
                key.append(f"{hero.name} (Инициатор)")
            elif any(r in ["Magnus", "Enigma", "Faceless Void"] for r in [hero.name]):
                key.append(f"{hero.name} (Teamfight)")
        
        return key[:3]
    
    def _find_counter_matchups(self, radiant: List[str], dire: List[str]) -> List[Dict]:
        """Поиск контрматчапов между командами"""
        matchups = []
        
        for rad_hero in radiant:
            rad = HeroService.find_hero(rad_hero)
            if not rad:
                continue
            
            for dire_hero in dire:
                dire_h = HeroService.find_hero(dire_hero)
                if not dire_h:
                    continue
                
                # Проверяем контрпики
                rad_weak = [w.lower() for w in rad.counters.weak_against]
                dire_weak = [w.lower() for w in dire_h.counters.weak_against]
                
                if dire_hero.lower() in rad_weak:
                    matchups.append({
                        "type": "bad_for_radiant",
                        "text": f"⚠️ {rad.name} слаб против {dire_h.name}",
                        "impact": -10
                    })
                elif rad_hero.lower() in dire_weak:
                    matchups.append({
                        "type": "good_for_radiant",
                        "text": f"✅ {rad.name} силен против {dire_h.name}",
                        "impact": +10
                    })
        
        return matchups[:5]
    
    def _calculate_win_probability(
        self, 
        rad: TeamAnalysis, 
        dire: TeamAnalysis,
        matchups: List[Dict]
    ) -> Tuple[float, float]:
        """Расчет вероятности победы"""
        
        # Базовые скоры
        rad_score = (
            rad.synergy_score * 0.35 +
            rad.draft_score * 0.25 +
            rad.meta_score * 0.20
        )
        
        dire_score = (
            dire.synergy_score * 0.35 +
            dire.draft_score * 0.25 +
            dire.meta_score * 0.20
        )
        
        # Учет контрматчапов
        matchup_bonus = sum(m.get("impact", 0) for m in matchups)
        rad_score += matchup_bonus * 0.2
        
        # Нормализация в вероятности
        total = rad_score + dire_score
        if total == 0:
            return 50.0, 50.0
        
        rad_prob = (rad_score / total) * 100
        dire_prob = 100 - rad_prob
        
        # Добавляем случайность для реализма (±3%)
        noise = random.uniform(-3, 3)
        rad_prob = max(5, min(95, rad_prob + noise))
        dire_prob = 100 - rad_prob
        
        return rad_prob, dire_prob
    
    def _determine_result(self, rad_prob: float, dire_prob: float) -> Tuple[PredictionResult, float]:
        """Определение результата и уверенности"""
        diff = abs(rad_prob - dire_prob)
        
        if diff < 5:
            return PredictionResult.UNCERTAIN, diff
        elif rad_prob > dire_prob:
            return PredictionResult.RADIANT_WIN, diff
        else:
            return PredictionResult.DIRE_WIN, diff
    
    def _extract_key_factors(
        self,
        rad: TeamAnalysis,
        dire: TeamAnalysis,
        rad_p: float,
        dire_p: float,
        matchups: List[Dict]
    ) -> List[str]:
        """Извлечение ключевых факторов"""
        factors = []
        
        # Сравнение синергий
        if rad.synergy_score > dire.synergy_score + 10:
            factors.append(f"🤝 Лучшая синергия у Света (+{rad.synergy_score - dire.synergy_score:.0f})")
        elif dire.synergy_score > rad.synergy_score + 10:
            factors.append(f"🤝 Лучшая синергия у Тьмы (+{dire.synergy_score - rad.synergy_score:.0f})")
        
        # Сравнение драфта
        if rad.draft_score > dire.draft_score + 10:
            factors.append("📋 Состав Света более сбалансирован")
        elif dire.draft_score > rad.draft_score + 10:
            factors.append("📋 Состав Тьмы более сбалансирован")
        
        # Мета
        if rad.meta_score > dire.meta_score + 10:
            factors.append("📈 Пик Света сильнее в текущей мете")
        elif dire.meta_score > rad.meta_score + 10:
            factors.append("📈 Пик Тьмы сильнее в текущей мете")
        
        # Контрматчапы
        good_matchups = [m for m in matchups if m["type"] == "good_for_radiant"]
        bad_matchups = [m for m in matchups if m["type"] == "bad_for_radiant"]
        
        if good_matchups:
            factors.append(f"🎯 {len(good_matchups)} выигрышных матчапа у Света")
        if bad_matchups:
            factors.append(f"⚠️ {len(bad_matchups)} проигрышных матчапа у Света")
        
        return factors[:4]
    
    def _extract_risks(
        self,
        radiant: List[str],
        dire: List[str],
        rad: TeamAnalysis,
        dire_a: TeamAnalysis
    ) -> List[str]:
        """Извлечение рисков"""
        risks = []
        
        if len(radiant) < 5:
            risks.append(f"⚠️ Состав Света неполный ({len(radiant)}/5)")
        if len(dire) < 5:
            risks.append(f"⚠️ Состав Тьмы неполный ({len(dire)}/5)")
        
        if not rad.strengths:
            risks.append("⚠️ У Света нет явных сильных сторон")
        if not dire_a.strengths:
            risks.append("⚠️ У Тьмы нет явных сильных сторон")
        
        return risks

# ==================== ОБРАБОТЧИКИ ====================

class CommandHandlers:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        text = f"""🎮 *Dota 2 Counter Bot v2.1*

Привет, {user.first_name}!

*Команды:*
• `/hero [имя]` — информация о герое (30+ героев)
• `/predict [A] vs [B]` — ML-предсказание победителя
• `/counter [имя]` — контрпики
• `/build [имя]` — рекомендуемый билд
• `/list` — список героев
• `/help` — помощь

Просто напиши имя героя!"""
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """📚 *Команды:*

/hero [имя] — информация о герое
/counter [имя] — контрпики
/predict [A] vs [B] — ML-предсказание матча
/build [имя] — рекомендуемый билд
/list — все герои в базе

*Пример предсказания:*
`/predict kez void slardar vs muerta ember tide`"""
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def list_heroes(update: Update, context: ContextTypes.DEFAULT_TYPE):
        heroes = HeroService.get_all_heroes()
        
        by_role = {}
        for hero in heroes:
            main_role = hero.roles[0]
            by_role.setdefault(main_role, []).append(hero.name)
        
        lines = [f"📋 *Героев в базе: {len(heroes)}*\n"]
        
        for role, names in sorted(by_role.items()):
            lines.append(f"*{role}:* {', '.join(sorted(names))}")
        
        text = "\n".join(lines)
        
        # Разбиваем если длинно
        if len(text) > 4000:
            for i in range(0, len(lines), 15):
                part = "\n".join(lines[i:i+15])
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
        heroes_count = len(HeroService.get_all_heroes())
        text = f"""🤖 *Dota 2 Counter Bot v2.1*

Героев в базе: *{heroes_count}*
ML-предиктор: ✅ Активен
Функции: контрпики, билды, предсказания

Создано для комьюнити Dota 2"""
        await update.message.reply_text(text, parse_mode='Markdown')

class HeroHandlers:
    @staticmethod
    def _create_keyboard(hero_name: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🛡️ Контрпики", callback_data=f"counter:{hero_name}"),
                InlineKeyboardButton("⚔️ Билд", callback_data=f"build:{hero_name}")
            ],
            [InlineKeyboardButton("🔄 Другие герои", callback_data="list")]
        ])
    
    @staticmethod
    async def hero_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Укажи имя героя: `/hero kez`", parse_mode='Markdown')
            return
        
        query = " ".join(context.args)
        await HeroHandlers._show_hero(update, context, query)
    
    @staticmethod
    async def counter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Укажи имя героя: `/counter muerta`", parse_mode='Markdown')
            return
        
        hero = HeroService.find_hero(" ".join(context.args))
        if not hero:
            await update.message.reply_text("❌ Герой не найден")
            return
        
        text = HeroService.format_counters(hero)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"hero:{hero.name}")]])
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    @staticmethod
    async def build_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Укажи имя героя: `/build void spirit`", parse_mode='Markdown')
            return
        
        hero = HeroService.find_hero(" ".join(context.args))
        if not hero:
            await update.message.reply_text("❌ Герой не найден")
            return
        
        text = HeroService.format_build(hero)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"hero:{hero.name}")]])
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    @staticmethod
    async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Укажи запрос: `/search void`", parse_mode='Markdown')
            return
        
        matches = HeroService.search_heroes(" ".join(context.args))
        
        if not matches:
            await update.message.reply_text("❌ Ничего не найдено")
            return
        
        if len(matches) == 1:
            await HeroHandlers._show_hero(update, context, matches[0].name)
            return
        
        keyboard = [[InlineKeyboardButton(h.name, callback_data=f"hero:{h.name}")] for h in matches]
        await update.message.reply_text("🔍 Найдено:", reply_markup=InlineKeyboardMarkup(keyboard))
    
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
                keyboard = [[InlineKeyboardButton(h.name, callback_data=f"hero:{h.name}")] for h in matches[:5]]
                await update.message.reply_text("🤔 Несколько вариантов:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(f"❓ Не нашел '{text}'. Используй `/search` или `/list`")
    
    @staticmethod
    async def _show_hero(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, is_callback: bool = False):
        hero = HeroService.find_hero(query)
        
        if not hero:
            text = f"❌ Герой '{query}' не найден"
            if is_callback:
                await update.callback_query.edit_message_text(text)
            else:
                await update.message.reply_text(text)
            return
        
        text = HeroService.format_hero_info(hero)
        keyboard = HeroHandlers._create_keyboard(hero.name)
        
        if is_callback:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
        else:
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)

class PredictionHandlers:
    async def predict_quick(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи составы:\n`/predict kez void slardar vs muerta ember tide`",
                parse_mode='Markdown'
            )
            return
        
        args = " ".join(context.args).lower()
        
        if " vs " not in args:
            await update.message.reply_text("❌ Раздели команды словом `vs`")
            return
        
        parts = args.split(" vs ")
        if len(parts) != 2:
            await update.message.reply_text("❌ Нужно 2 команды")
            return
        
        radiant = [h.strip() for h in parts[0].split() if h.strip()]
        dire = [h.strip() for h in parts[1].split() if h.strip()]
        
        # Валидация
        valid_rad, errors_rad = self._validate(radiant)
        valid_dire, errors_dire = self._validate(dire)
        
        if errors_rad or errors_dire:
            text = "❌ *Ошибки в названиях:*\n" + "\n".join(errors_rad + errors_dire)
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        await self._make_prediction(update, valid_rad, valid_dire)
    
    def _validate(self, heroes: List[str]) -> Tuple[List[str], List[str]]:
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
    
    async def _make_prediction(self, update: Update, radiant: List[str], dire: List[str]):
        msg = await update.message.reply_text("🔮 Анализирую составы...")
        
        try:
            predictor = MatchPredictor()
            pred = await predictor.predict(radiant, dire)
            
            text = self._format_prediction(pred)
            
            # Callback data (короткий)
            rad_key = ",".join([h[:3] for h in radiant])
            dire_key = ",".join([h[:3] for h in dire])
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Детали", callback_data=f"d:{rad_key}:{dire_key}")],
                [InlineKeyboardButton("🔄 Новый анализ", callback_data="new")]
            ])
            
            await msg.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            await msg.edit_text("❌ Ошибка анализа")
    
    def _format_prediction(self, pred: MatchPrediction) -> str:
        lines = [
            "🔮 *ПРЕДСКАЗАНИЕ МАТЧА (ML)*",
            "",
            f"🟢 *Свет:* {', '.join(pred.radiant.heroes)}",
            f"🔴 *Тьма:* {', '.join(pred.dire.heroes)}",
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
        
        # ML метрики
        lines.extend([
            "",
            f"*📈 ML Метрики:*",
            f"Синергия Света: {pred.radiant.synergy_score:.0f}/100",
            f"Синергия Тьмы: {pred.dire.synergy_score:.0f}/100",
            f"Драфт Света: {pred.radiant.draft_score:.0f}/100",
            f"Драфт Тьмы: {pred.dire.draft_score:.0f}/100"
        ])
        
        lines.append("")
        lines.append("_Анализ: синергии, контрпики, мета, драфт_")
        
        return "\n".join(lines)

class StatsHandlers:
    @staticmethod
    async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📊 Используй `/hero [имя]` для статистики героя")
    
    @staticmethod
    async def meta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        heroes = HeroService.get_all_heroes()
        top = sorted([h for h in heroes if h.stats], key=lambda h: {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}.get(h.stats.tier, 0), reverse=True)[:10]
        
        lines = ["🌍 *Топ героев по тирам:*\n"]
        for h in top:
            tier_emoji = {"S": "🔴", "A": "🟠", "B": "🟡", "C": "🟢", "D": "⚪"}.get(h.stats.tier, "❓")
            lines.append(f"{tier_emoji} *{h.name}* — {h.roles[0]} ({h.stats.win_rate}%)")
        
        await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
    
    @staticmethod
    async def counters_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Укажи имя героя: `/counters kez`")
            return
        
        hero = HeroService.find_hero(" ".join(context.args))
        if not hero:
            await update.message.reply_text("❌ Герой не найден")
            return
        
        text = HeroService.format_counters(hero)
        await update.message.reply_text(text, parse_mode='Markdown')

class CallbackHandlers:
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        try:
            if data.startswith("hero:"):
                hero_name = data.split(":", 1)[1]
                await HeroHandlers._show_hero(update, context, hero_name, is_callback=True)
            
            elif data.startswith("counter:"):
                hero_name = data.split(":", 1)[1]
                hero = HeroService.find_hero(hero_name)
                if hero:
                    text = HeroService.format_counters(hero)
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"hero:{hero.name}")]])
                    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
            
            elif data.startswith("build:"):
                hero_name = data.split(":", 1)[1]
                hero = HeroService.find_hero(hero_name)
                if hero:
                    text = HeroService.format_build(hero)
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"hero:{hero.name}")]])
                    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
            
            elif data == "list":
                heroes = HeroService.get_all_heroes()
                by_role = {}
                for h in heroes:
                    by_role.setdefault(h.roles[0], []).append(h.name)
                
                keyboard = []
                for role, names in sorted(by_role.items())[:6]:
                    row = []
                    for name in sorted(names)[:3]:
                        row.append(InlineKeyboardButton(name, callback_data=f"hero:{name}"))
                    if row:
                        keyboard.append(row)
                
                await query.edit_message_text("📋 *Выбери героя:*", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            
            elif data == "new":
                await query.edit_message_text("🔮 Введи: `/predict [свет] vs [тьма]`", parse_mode='Markdown')
        
        except Exception as e:
            logger.error(f"Callback error: {e}")

class ErrorHandlers:
    @staticmethod
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Update {update} caused error {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

# ==================== СОЗДАНИЕ ПРИЛОЖЕНИЯ ====================

def create_application():
    logger.info("Creating bot application...")
    
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is empty!")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    predict_handlers = PredictionHandlers()
    
    # Команды
    app.add_handler(CommandHandler("start", CommandHandlers.start))
    app.add_handler(CommandHandler("help", CommandHandlers.help_command))
    app.add_handler(CommandHandler("list", CommandHandlers.list_heroes))
    app.add_handler(CommandHandler("about", CommandHandlers.about))
    
    # Герои
    app.add_handler(CommandHandler("hero", HeroHandlers.hero_command))
    app.add_handler(CommandHandler("counter", HeroHandlers.counter_command))
    app.add_handler(CommandHandler("build", HeroHandlers.build_command))
    app.add_handler(CommandHandler("search", HeroHandlers.search_command))
    
    # Статистика и предсказания
    app.add_handler(CommandHandler("stats", StatsHandlers.stats_command))
    app.add_handler(CommandHandler("meta", StatsHandlers.meta_command))
    app.add_handler(CommandHandler("counters", StatsHandlers.counters_stats_command))
    app.add_handler(CommandHandler("predict", predict_handlers.predict_quick))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(CallbackHandlers.handle_callback))
    
    # Текст
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, HeroHandlers.handle_text))
    
    # Ошибки
    app.add_error_handler(ErrorHandlers.error_handler)
    
    logger.info("Bot application created")
    return app

# ==================== ЗАПУСК ====================

async def main():
    logger.info("=" * 50)
    logger.info("Dota 2 Counter Bot v2.1")
    logger.info(f"Heroes: {len(HEROES_DATABASE)} | ML Predictor: Active")
    logger.info("=" * 50)
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        return
    
    try:
        application = create_application()
        await application.initialize()
        await application.start()
        
        logger.info("Bot started! Polling...")
        
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        
        while True:
            await asyncio.sleep(60)
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.critical(f"Fatal: {e}")
        sys.exit(1)
