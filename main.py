#!/usr/bin/env python3
"""
Dota 2 Counter Bot v2.0 - All-in-One Version
Telegram бот с ML-предсказаниями матчей, контрпиками и статистикой
"""

import asyncio
import logging
import sys
import os
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

# Загрузка .env (если есть)
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

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== МОДЕЛИ ДАННЫХ ====================

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
            return "🟢 Низкая (равные шансы)"

# ==================== БАЗА ДАННЫХ ГЕРОЕВ ====================

HEROES_DATABASE = {
    "kez": Hero(
        id="kez",
        name="Kez",
        localized_name="Kez",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Escape", "Nuker"],
        description="Мобильный agility-carry с высоким взрывным уроном и двумя стилями боя.",
        strengths=["Высокая мобильность", "Взрывной урон", "Два режима атаки", "Сильный в мид-гейме"],
        weaknesses=["Зависим от предметов", "Сложная механика", "Уязвим к контролю", "Проблемы против иллюзий"],
        counters=HeroCounters(
            strong_against=["Sniper", "Drow Ranger", "Crystal Maiden", "Shadow Shaman"],
            weak_against=["Phantom Lancer", "Chaos Knight", "Tidehunter", "Axe", "Puck"],
            counter_items=["Ghost Scepter", "Eul's Scepter", "Heaven's Halberd", "Force Staff", "Black King Bar", "Silver Edge"],
            core_items=["Echo Sabre / Disperser", "Black King Bar", "Daedalus / Bloodthorn", "Satanic", "Butterfly"],
            countered_by={
                "heroes": ["Phantom Lancer", "Meepo", "Naga Siren"],
                "items": ["Silver Edge", "Bloodthorn", "Orchid Malevolence"],
                "description": "Покупайте Silver Edge для брейка пассивки, Bloodthorn для true strike."
            }
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Healing Salve", "Quelling Blade", "Circlet", "3x Iron Branch"],
            early_game=["Power Treads", "Magic Wand", "Echo Sabre"],
            mid_game=["Black King Bar", "Disperser", "Crystalys"],
            late_game=["Daedalus", "Satanic", "Butterfly", "Swift Blink"],
            situational=["Bloodthorn", "Monkey King Bar", "Abyssal Blade", "Nullifier"]
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
        description="Гибридный carry с магическим и физическим уроном. Сильный лейт-гейм carry с формой призрака.",
        strengths=["Огромный урон в лейте", "Форма призрака", "Смешанный тип урона", "Сильная ультимейт-форма"],
        weaknesses=["Медленный фарм", "Уязвима до BKB", "Зависит от позиционирования", "Контрится silence"],
        counters=HeroCounters(
            strong_against=["Terrorblade", "Naga Siren", "Spectre", "Anti-Mage"],
            weak_against=["Anti-Mage", "Nyx Assassin", "Silencer", "Phantom Assassin"],
            counter_items=["Bloodthorn", "Silver Edge", "Orchid Malevolence", "Scythe of Vyse", "Black King Bar", "Manta Style"],
            core_items=["Maelstrom / Mjollnir", "Black King Bar", "Gleipnir", "Daedalus", "Satanic", "Bloodthorn"],
            countered_by={
                "heroes": ["Anti-Mage", "Silencer", "Nyx Assassin"],
                "items": ["Bloodthorn", "Silver Edge", "Orchid Malevolence", "Scythe of Vyse"],
                "description": "Silencer ult отключает способности. Bloodthorn для true strike против уклонения."
            }
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Healing Salve", "Circlet", "Branches"],
            early_game=["Power Treads", "Magic Wand", "Maelstrom"],
            mid_game=["Black King Bar", "Gleipnir", "Dragon Lance"],
            late_game=["Daedalus", "Satanic", "Bloodthorn", "Hurricane Pike"],
            situational=["Monkey King Bar", "Silver Edge", "Refresher Orb"]
        ),
        stats=HeroStats(win_rate=51.8, pick_rate=12.5, tier="A")
    ),
    
    "void_spirit": Hero(
        id="void_spirit",
        name="Void Spirit",
        localized_name="Void Spirit",
        primary_attr="int",
        attack_type="Melee",
        roles=["Carry", "Escape", "Nuker", "Disabler"],
        description="Мобильный mid-герой с высоким взрывным уроном и манипуляцией пространством.",
        strengths=["Высокая мобильность", "Взрывной магический урон", "Сложно поймать", "Сильный в дайвах"],
        weaknesses=["Уязвим к silence", "Нужна мана", "Падает в лейте", "Требует механики"],
        counters=HeroCounters(
            strong_against=["Sniper", "Shadow Fiend", "Storm Spirit", "Ember Spirit"],
            weak_against=["Silencer", "Doom", "Bloodseeker", "Anti-Mage"],
            counter_items=["Orchid Malevolence", "Bloodthorn", "Scythe of Vyse", "Abyssal Blade", "Eul's Scepter", "Black King Bar"],
            core_items=["Bottle", "Kaya and Sange", "Orchid Malevolence / Bloodthorn", "Black King Bar", "Aghanim's Scepter", "Refresher Orb"],
            countered_by={
                "heroes": ["Silencer", "Doom", "Bloodseeker"],
                "items": ["Orchid Malevolence", "Bloodthorn", "Scythe of Vyse", "Abyssal Blade"],
                "description": "Ловите Orchid/Bloodthorn когда он использует способности."
            }
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Circlet", "Branches", "Faerie Fire"],
            early_game=["Bottle", "Power Treads", "Magic Wand", "Kaya"],
            mid_game=["Orchid Malevolence", "Black King Bar", "Sange and Kaya"],
            late_game=["Bloodthorn", "Refresher Orb", "Octarine Core", "Aghanim's Scepter"],
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
        description="Мобильный carry с физическим и магическим уроном. Сложный в освоении, но невероятно сильный.",
        strengths=["Высочайшая мобильность", "Смешанный урон", "Силен на всех стадиях", "Remnant для escape/initiate"],
        weaknesses=["Уязвим к silence", "Требует маны", "Сложная механика", "Контрится hard disable"],
        counters=HeroCounters(
            strong_against=["Nature's Prophet", "Anti-Mage", "Broodmother", "Tinker"],
            weak_against=["Silencer", "Faceless Void", "Storm Spirit", "Void Spirit"],
            counter_items=["Orchid Malevolence", "Bloodthorn", "Scythe of Vyse", "Abyssal Blade", "Silver Edge", "Eul's Scepter"],
            core_items=["Bottle", "Phase Boots", "Maelstrom / Mjollnir", "Black King Bar", "Daedalus", "Octarine Core"],
            countered_by={
                "heroes": ["Silencer", "Faceless Void", "Storm Spirit"],
                "items": ["Orchid Malevolence", "Bloodthorn", "Scythe of Vyse"],
                "description": "Silencer и Faceless Void контрят его мобильность."
            }
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
    
    "slardar": Hero(
        id="slardar",
        name="Slardar",
        localized_name="Slardar",
        primary_attr="str",
        attack_type="Melee",
        roles=["Carry", "Durable", "Initiator", "Disabler", "Escape"],
        description="Сильный инициатор с минус броней и мобильностью. Отличный дайвер.",
        strengths=["Сильная инициация", "Минус броня", "Высокая мобильность", "Bash против крипов"],
        weaknesses=["Уязвим к kiting'у", "Проблемы против иллюзий", "Требует Blink", "Слаб без предметов"],
        counters=HeroCounters(
            strong_against=["Alchemist", "Anti-Mage", "Spectre", "Wraith King"],
            weak_against=["Phantom Lancer", "Terrorblade", "Naga Siren", "Tinker"],
            counter_items=["Force Staff", "Ghost Scepter", "Eul's Scepter", "Glimmer Cape", "Silver Edge", "Diffusal Blade"],
            core_items=["Phase Boots", "Blink Dagger", "Black King Bar", "Aghanim's Scepter", "Assault Cuirass", "Shiva's Guard"],
            countered_by={
                "heroes": ["Phantom Lancer", "Terrorblade", "Anti-Mage"],
                "items": ["Silver Edge", "Bloodthorn", "Diffusal Blade"],
                "description": "Silver Edge брейкает пассивку. PL/TB не боятся минус брони."
            }
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Healing Salve", "Quelling Blade", "Shield"],
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
        description="Мощный танк с лучшим AoE контролем в игре (Ravage).",
        strengths=["Ravage - лучший AoE стан", "Высокая живучесть", "Anchor Smash против крипов", "Сильный на всех стадиях"],
        weaknesses=["Долгий кд на Ravage", "Уязвим к silence", "Мана зависимость", "Медленный фарм"],
        counters=HeroCounters(
            strong_against=["Phantom Assassin", "Anti-Mage", "Spectre", "Faceless Void"],
            weak_against=["Silencer", "Enigma", "Rubick", "Doom"],
            counter_items=["Black King Bar", "Linken's Sphere", "Lotus Orb", "Guardian Greaves", "Silver Edge", "Diffusal Blade"],
            core_items=["Arcane Boots", "Blink Dagger", "Black King Bar", "Refresher Orb", "Shiva's Guard", "Lotus Orb"],
            countered_by={
                "heroes": ["Silencer", "Enigma", "Rubick"],
                "items": ["Silver Edge", "Diffusal Blade", "Abyssal Blade"],
                "description": "Silencer ult, Enigma Black Hole — контрпики Ravage."
            }
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Healing Salve", "Clarity", "Shield"],
            early_game=["Arcane Boots", "Magic Wand", "Blink Dagger"],
            mid_game=["Black King Bar", "Force Staff", "Mekansm"],
            late_game=["Refresher Orb", "Shiva's Guard", "Lotus Orb", "Guardian Greaves"],
            situational=["Pipe of Insight", "Crimson Guard", "Aghanim's Scepter"]
        ),
        stats=HeroStats(win_rate=50.1, pick_rate=10.2, tier="A")
    ),
    
    "shadow_shaman": Hero(
        id="shadow_shaman",
        name="Shadow Shaman",
        localized_name="Shadow Shaman",
        primary_attr="int",
        attack_type="Ranged",
        roles=["Support", "Pusher", "Disabler", "Nuker", "Initiator"],
        description="Сильнейший пушер и дизейблер с длиннейшим станом в игре.",
        strengths=["Длинный стан", "Мощный пуш", "Hex для дизейбла", "Сильный в ранней игре"],
        weaknesses=["Очень хрупкий", "Медленный", "Зависим от позиционирования", "Легко убивается"],
        counters=HeroCounters(
            strong_against=["Morphling", "Anti-Mage", "Spectre", "Wraith King"],
            weak_against=["Pudge", "Clockwerk", "Spirit Breaker", "Night Stalker"],
            counter_items=["Force Staff", "Glimmer Cape", "Ghost Scepter", "Black King Bar", "Lotus Orb", "Eul's Scepter"],
            core_items=["Arcane Boots", "Aether Lens", "Aghanim's Scepter", "Glimmer Cape", "Force Staff", "Refresher Orb"],
            countered_by={
                "heroes": ["Pudge", "Clockwerk", "Spirit Breaker", "Night Stalker"],
                "items": ["Force Staff", "Glimmer Cape", "Ghost Scepter"],
                "description": "Покупайте мобильность чтобы спастись от гэпклоуеров."
            }
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Healing Salve", "Clarity", "Observer Ward", "Sentry Ward"],
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
        description="Сильный support с мощным ультимейтом и полезными способностями для команды.",
        strengths=["Chain Frost - разрыв в файтах", "Ice Armor - защита", "Sacrifice - контроль линии", "Сильный в ранней игре"],
        weaknesses=["Хрупкий", "Мана зависимость", "Уязвим к мана-бёрну", "Chain Frost требует позиционирования"],
        counters=HeroCounters(
            strong_against=["Broodmother", "Chaos Knight", "Meepo", "Phantom Lancer"],
            weak_against=["Anti-Mage", "Nyx Assassin", "Pugna", "Morphling"],
            counter_items=["Black King Bar", "Glimmer Cape", "Force Staff", "Lotus Orb", "Pipe of Insight", "Blade Mail"],
            core_items=["Tranquil Boots", "Magic Wand", "Glimmer Cape", "Aghanim's Scepter", "Force Staff", "Ghost Scepter"],
            countered_by={
                "heroes": ["Anti-Mage", "Nyx Assassin", "Pugna"],
                "items": ["Force Staff", "Glimmer Cape", "Ghost Scepter"],
                "description": "Anti-Mage сжигает ману, Nyx взрывает Frost Blast."
            }
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Healing Salve", "Mango", "Observer Ward"],
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
        description="Сильный дизейблер с мощным ультимейтом и несколькими станами.",
        strengths=["Два disables", "Finger of Death", "Mana Drain", "Сильный в ганках"],
        weaknesses=["Очень хрупкий", "Медленный", "Зависим от позиционирования", "Finger of Death имеет задержку"],
        counters=HeroCounters(
            strong_against=["Morphling", "Anti-Mage", "Storm Spirit", "Wraith King"],
            weak_against=["Nyx Assassin", "Pudge", "Clockwerk", "Lifestealer"],
            counter_items=["Force Staff", "Glimmer Cape", "Black King Bar", "Lotus Orb", "Linken's Sphere", "Ghost Scepter"],
            core_items=["Tranquil Boots", "Blink Dagger", "Aether Lens", "Aghanim's Scepter", "Force Staff", "Glimmer Cape"],
            countered_by={
                "heroes": ["Nyx Assassin", "Pudge", "Clockwerk"],
                "items": ["Force Staff", "Glimmer Cape", "Ghost Scepter"],
                "description": "Nyx отражает Finger of Death. Pudge разрывает позиционирование."
            }
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Healing Salve", "Clarity", "Observer Ward"],
            early_game=["Tranquil Boots", "Magic Wand", "Wind Lace"],
            mid_game=["Blink Dagger", "Aether Lens", "Force Staff"],
            late_game=["Aghanim's Scepter", "Octarine Core", "Refresher Orb", "Glimmer Cape"],
            situational=["Aeon Disk", "Ghost Scepter", "Lotus Orb"]
        ),
        stats=HeroStats(win_rate=47.8, pick_rate=13.5, tier="B")
    ),
    
    "phantom_lancer": Hero(
        id="phantom_lancer",
        name="Phantom Lancer",
        localized_name="Phantom Lancer",
        primary_attr="agi",
        attack_type="Melee",
        roles=["Carry", "Escape", "Pusher", "Nuker"],
        description="Carry, создающий армию иллюзий. Сильнейший лейт-гейм carry.",
        strengths=["Армия иллюзий", "Высокая мобильность", "Сложно найти настоящего", "Невероятный лейт"],
        weaknesses=["Слаб рано", "Уязвим к AoE", "Требует фарма", "Контрится item'ами"],
        counters=HeroCounters(
            strong_against=["Slardar", "Tidehunter", "Sven", "Ursa"],
            weak_against=["Axe", "Earthshaker", "Sven", "Medusa"],
            counter_items=["Battle Fury", "Mjollnir", "Radiance", "Shiva's Guard", "Gleipnir", "Dragon Lance"],
            core_items=["Power Treads", "Diffusal Blade", "Manta Style", "Heart of Tarrasque", "Butterfly", "Satanic"],
            countered_by={
                "heroes": ["Axe", "Earthshaker", "Sven"],
                "items": ["Battle Fury", "Mjollnir", "Radiance", "Shiva's Guard"],
                "description": "AoE урон уничтожает иллюзии. Battle Fury лучший контр."
            }
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Quelling Blade", "Circlet", "Branches"],
            early_game=["Power Treads", "Wraith Band", "Diffusal Blade"],
            mid_game=["Manta Style", "Heart of Tarrasque", "Butterfly"],
            late_game=["Satanic", "Bloodthorn", "Skadi", "Boots of Travel"],
            situational=["Black King Bar", "Silver Edge", "Monkey King Bar"]
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
        description="Быстрый фармер с мана-бёрном. Сильнейший лейт-гейм carry против магов.",
        strengths=["Быстрый фарм", "Мана Break против магов", "Blink для escape", "Сильный лейт"],
        weaknesses=["Слаб рано", "Требует много фарма", "Уязвим к контролю", "Проблемы против силы"],
        counters=HeroCounters(
            strong_against=["Lich", "Lion", "Zeus", "Storm Spirit"],
            weak_against=["Phantom Assassin", "Legion Commander", "Meepo", "Chaos Knight"],
            counter_items=["Silver Edge", "Bloodthorn", "Orchid Malevolence", "Scythe of Vyse", "Legion Commander", "Phantom Assassin"],
            core_items=["Power Treads", "Battle Fury", "Manta Style", "Butterfly", "Black King Bar", "Abyssal Blade"],
            countered_by={
                "heroes": ["Phantom Assassin", "Legion Commander", "Meepo"],
                "items": ["Silver Edge", "Bloodthorn", "Orchid Malevolence", "Scythe of Vyse"],
                "description": "Заканчивайте игру до 30 минуты. Legion Duel игнорирует BKB."
            }
        ),
        builds=HeroBuild(
            starting_items=["Tango", "Healing Salve", "Quelling Blade", "Shield"],
            early_game=["Power Treads", "Magic Wand", "Ring of Health"],
            mid_game=["Battle Fury", "Manta Style", "Black King Bar"],
            late_game=["Butterfly", "Abyssal Blade", "Satanic", "Heart of Tarrasque"],
            situational=["Monkey King Bar", "Bloodthorn", "Nullifier"]
        ),
        stats=HeroStats(win_rate=49.5, pick_rate=12.1, tier="B")
    ),
}

HEROES_BY_NAME = {}
for hero_id, hero in HEROES_DATABASE.items():
    HEROES_BY_NAME[hero_id] = hero
    HEROES_BY_NAME[hero.name.lower()] = hero
    if hero.localized_name:
        HEROES_BY_NAME[hero.localized_name.lower()] = hero

# ==================== СЕРВИСЫ ====================

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

# ==================== ML ПРЕДИКТОР ====================

class MatchPredictor:
    WEIGHTS = {
        "win_rate": 0.25,
        "synergy": 0.20,
        "counter": 0.25,
        "draft": 0.15,
        "meta": 0.15
    }
    
    SYNERGIES = {
        ("slardar", "spectre"): 15,
        ("dazzle", "axe"): 12,
        ("magnus", "melee_carry"): 10,
        ("dark_seer", "melee_carry"): 10,
        ("crystal_maiden", "mana_hungry"): 8,
        ("omniknight", "melee_core"): 8,
        ("shadow_shaman", "pusher"): 10,
        ("lich", "teamfight"): 8,
    }
    
    def __init__(self):
        pass
    
    async def predict(self, radiant: List[str], dire: List[str]) -> MatchPrediction:
        radiant_analysis = await self._analyze_team(radiant, "Radiant")
        dire_analysis = await self._analyze_team(dire, "Dire")
        
        counter_matchups = self._analyze_counter_matchups(radiant, dire)
        
        rad_prob, dire_prob = self._calculate_probabilities(
            radiant_analysis, dire_analysis, counter_matchups
        )
        
        result, confidence = self._determine_result(rad_prob, dire_prob)
        
        key_factors = self._extract_key_factors(
            radiant_analysis, dire_analysis, rad_prob, dire_prob
        )
        
        return MatchPrediction(
            radiant=radiant_analysis,
            dire=dire_analysis,
            result=result,
            confidence=confidence,
            win_probability_radiant=rad_prob,
            win_probability_dire=dire_prob,
            key_factors=key_factors,
            risk_factors=self._extract_risks(radiant_analysis, dire_analysis),
            counter_matchups=counter_matchups
        )
    
    async def _analyze_team(self, heroes: List[str], team_name: str) -> TeamAnalysis:
        synergy = self._calculate_synergy(heroes)
        draft = self._evaluate_draft(heroes)
        meta = self._evaluate_meta_score(heroes)
        
        strengths, weaknesses = self._analyze_strengths_weaknesses(heroes)
        key_heroes = self._identify_key_heroes(heroes)
        
        win_prob = (synergy + draft + meta) / 3
        
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
        if len(heroes) < 2:
            return 50.0
            
        score = 50.0
        hero_ids = [h.lower().replace(" ", "_") for h in heroes]
        
        for (h1, h2), bonus in self.SYNERGIES.items():
            if h1 in hero_ids and h2 in hero_ids:
                score += bonus
            elif h2 in hero_ids and h1 in hero_ids:
                score += bonus
        
        # Бонус за баланс
        has_carry = any(HeroService.find_hero(h) and "Carry" in HeroService.find_hero(h).roles for h in heroes)
        has_init = any(HeroService.find_hero(h) and any(r in HeroService.find_hero(h).roles for r in ["Initiator", "Disabler"]) for h in heroes)
        
        if has_carry and has_init:
            score += 10
        
        return max(0, min(100, score))
    
    def _evaluate_draft(self, heroes: List[str]) -> float:
        score = 50.0
        
        if len(heroes) < 2:
            return score
        
        has_carry = False
        has_init = False
        melee = 0
        ranged = 0
        
        for h in heroes:
            hero = HeroService.find_hero(h)
            if not hero:
                continue
            if "Carry" in hero.roles:
                has_carry = True
            if any(r in hero.roles for r in ["Initiator", "Disabler"]):
                has_init = True
            if hero.attack_type == "Melee":
                melee += 1
            else:
                ranged += 1
        
        if has_carry and has_init:
            score += 15
        if melee > 0 and ranged > 0:
            score += 10
        
        return max(0, min(100, score))
    
    def _evaluate_meta_score(self, heroes: List[str]) -> float:
        if not heroes:
            return 0
            
        total = 0
        for h in heroes:
            hero = HeroService.find_hero(h)
            if hero and hero.stats:
                tier_score = {"S": 100, "A": 85, "B": 70, "C": 55, "D": 40}.get(hero.stats.tier, 50)
                total += tier_score
            else:
                total += 50
                
        return total / len(heroes)
    
    def _analyze_strengths_weaknesses(self, heroes: List[str]) -> Tuple[List[str], List[str]]:
        strengths = []
        weaknesses = []
        
        has_carry = False
        has_init = False
        
        for h in heroes:
            hero = HeroService.find_hero(h)
            if not hero:
                continue
            if "Carry" in hero.roles:
                has_carry = True
            if any(r in hero.roles for r in ["Initiator", "Disabler"]):
                has_init = True
        
        if has_carry:
            strengths.append("✅ Есть керри для лейта")
        else:
            weaknesses.append("❌ Нет явного керри")
            
        if has_init:
            strengths.append("✅ Есть инициатор")
        else:
            weaknesses.append("❌ Нет инициатора")
        
        return strengths, weaknesses
    
    def _identify_key_heroes(self, heroes: List[str]) -> List[str]:
        key = []
        for h in heroes:
            hero = HeroService.find_hero(h)
            if not hero:
                continue
            if "Carry" in hero.roles:
                key.append(f"{hero.name} (Керри)")
            elif any(r in hero.roles for r in ["Initiator", "Disabler"]):
                key.append(f"{hero.name} (Инициатор)")
        return key[:3]
    
    def _analyze_counter_matchups(self, radiant: List[str], dire: List[str]) -> List[Dict]:
        matchups = []
        
        for rad_hero in radiant:
            for dire_hero in dire:
                rad = HeroService.find_hero(rad_hero)
                dire_h = HeroService.find_hero(dire_hero)
                
                if not rad or not dire_h:
                    continue
                    
                if dire_hero.lower() in [h.lower() for h in rad.counters.weak_against]:
                    matchups.append({
                        "type": "bad",
                        "text": f"⚠️ {rad.name} слаб против {dire_h.name}"
                    })
                elif rad_hero.lower() in [h.lower() for h in dire_h.counters.weak_against]:
                    matchups.append({
                        "type": "good",
                        "text": f"✅ {rad.name} силен против {dire_h.name}"
                    })
                    
        return matchups[:5]
    
    def _calculate_probabilities(self, rad: TeamAnalysis, dire: TeamAnalysis, matchups: List[Dict]) -> Tuple[float, float]:
        rad_score = rad.synergy_score * 0.3 + rad.draft_score * 0.3 + rad.meta_score * 0.2
        dire_score = dire.synergy_score * 0.3 + dire.draft_score * 0.3 + dire.meta_score * 0.2
        
        # Учет контрпиков
        good_matchups = sum(1 for m in matchups if m["type"] == "good")
        bad_matchups = sum(1 for m in matchups if m["type"] == "bad")
        
        counter_bonus = (good_matchups - bad_matchups) * 5
        rad_score += counter_bonus
        dire_score -= counter_bonus
        
        total = rad_score + dire_score
        if total == 0:
            return 50.0, 50.0
            
        rad_prob = (rad_score / total) * 100
        dire_prob = 100 - rad_prob
        
        # Шум для реализма
        noise = random.uniform(-3, 3)
        rad_prob = max(5, min(95, rad_prob + noise))
        dire_prob = 100 - rad_prob
        
        return rad_prob, dire_prob
    
    def _determine_result(self, rad_prob: float, dire_prob: float) -> Tuple[PredictionResult, float]:
        diff = abs(rad_prob - dire_prob)
        
        if diff < 5:
            return PredictionResult.UNCERTAIN, diff
        elif rad_prob > dire_prob:
            return PredictionResult.RADIANT_WIN, diff
        else:
            return PredictionResult.DIRE_WIN, diff
    
    def _extract_key_factors(self, rad: TeamAnalysis, dire: TeamAnalysis, rad_p: float, dire_p: float) -> List[str]:
        factors = []
        
        if rad.synergy_score > dire.synergy_score + 10:
            factors.append(f"🤝 Лучшая синергия у Света")
        elif dire.synergy_score > rad.synergy_score + 10:
            factors.append(f"🤝 Лучшая синергия у Тьмы")
            
        if rad.meta_score > dire.meta_score + 10:
            factors.append("📈 Пик Света сильнее в мете")
        elif dire.meta_score > rad.meta_score + 10:
            factors.append("📈 Пик Тьмы сильнее в мете")
            
        return factors
    
    def _extract_risks(self, rad: TeamAnalysis, dire: TeamAnalysis) -> List[str]:
        risks = []
        if len(rad.heroes) < 5:
            risks.append(f"⚠️ Состав Света неполный ({len(rad.heroes)}/5)")
        if len(dire.heroes) < 5:
            risks.append(f"⚠️ Состав Тьмы неполный ({len(dire.heroes)}/5)")
        return risks

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

class CommandHandlers:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        logger.info(f"User {user.id} started bot")
        
        text = f"""🎮 *Dota 2 Counter Bot*

Привет, {user.first_name}!

*Команды:*
• `/hero [имя]` — информация о герое
• `/predict [A] vs [B]` — предсказать победителя
• `/stats [имя]` — статистика
• `/meta` — текущая мета
• `/list` — список героев

Просто напиши имя героя!"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """📚 *Команды:*

/hero [имя] — информация о герое
/counter [имя] — контрпики
/predict [A] vs [B] — ML-предсказание
/stats [имя] — винрейт, тир
/meta — топ пиков
/search [запрос] — поиск
/list — все герои"""
        await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def list_heroes(update: Update, context: ContextTypes.DEFAULT_TYPE):
        heroes = HeroService.get_all_heroes()
        
        by_role = {}
        for hero in heroes:
            main_role = hero.roles[0]
            by_role.setdefault(main_role, []).append(hero.name)
        
        lines = ["📋 *Герои в базе:*\n"]
        for role, names in sorted(by_role.items()):
            lines.append(f"*{role}:* {', '.join(sorted(names))}")
        
        text = "\n".join(lines)
        
        if len(text) > 4000:
            # Разбиваем на части
            for i in range(0, len(lines), 20):
                part = "\n".join(lines[i:i+20])
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')
    
    @staticmethod
    async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
        heroes_count = len(HeroService.get_all_heroes())
        text = f"""🤖 *Dota 2 Counter Bot v2.0*

Героев в базе: {heroes_count}
Функции: контрпики, билды, ML-предсказания

Создано для комьюнити Dota 2"""
        await update.message.reply_text(text, parse_mode='Markdown')

class HeroHandlers:
    @staticmethod
    def _create_keyboard(hero_name: str) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("🛡️ Контрпики", callback_data=f"counter:{hero_name}"),
                InlineKeyboardButton("⚔️ Билд", callback_data=f"build:{hero_name}")
            ],
            [InlineKeyboardButton("🔄 Другие герои", callback_data="list")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
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
        
        query = " ".join(context.args)
        hero = HeroService.find_hero(query)
        
        if not hero:
            await update.message.reply_text(f"❌ Герой '{query}' не найден")
            return
        
        text = HeroService.format_counters(hero)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"hero:{hero.name}")]])
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    @staticmethod
    async def build_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Укажи имя героя: `/build void spirit`", parse_mode='Markdown')
            return
        
        query = " ".join(context.args)
        hero = HeroService.find_hero(query)
        
        if not hero:
            await update.message.reply_text(f"❌ Герой '{query}' не найден")
            return
        
        text = HeroService.format_build(hero)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data=f"hero:{hero.name}")]])
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    @staticmethod
    async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Укажи запрос: `/search void`", parse_mode='Markdown')
            return
        
        query = " ".join(context.args)
        matches = HeroService.search_heroes(query)
        
        if not matches:
            await update.message.reply_text(f"❌ По запросу '{query}' ничего не найдено")
            return
        
        if len(matches) == 1:
            await HeroHandlers._show_hero(update, context, matches[0].name)
            return
        
        keyboard = [[InlineKeyboardButton(h.name, callback_data=f"hero:{h.name}")] for h in matches]
        await update.message.reply_text(f"🔍 Найдено:", reply_markup=InlineKeyboardMarkup(keyboard))
    
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
                await update.message.reply_text(f"🤔 Несколько вариантов:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(f"❓ Не нашел '{text}'. Используй `/search` или `/list`")
    
    @staticmethod
    async def _show_hero(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, is_callback: bool = False):
        hero = HeroService.find_hero(query)
        
        if not hero:
            matches = HeroService.search_heroes(query)
            if matches:
                suggestions = ", ".join([h.name for h in matches[:3]])
                text = f"❌ Не найдено. Возможно: {suggestions}?"
            else:
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
                "❌ Укажи составы: `/predict kez void slardar vs muerta ember tide`",
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
            text = "❌ *Ошибки:*\n" + "\n".join(errors_rad + errors_dire)
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
            
            text = self._format(pred)
            
            # Создаем callback data
            rad_str = ",".join(radiant)
            dire_str = ",".join(dire)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Детали", callback_data=f"details:{rad_str}:{dire_str}")],
                [InlineKeyboardButton("🔄 Новый анализ", callback_data="predict_new")]
            ])
            
            await msg.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            await msg.edit_text("❌ Ошибка анализа")
    
    def _format(self, pred: MatchPrediction) -> str:
        lines = [
            "🔮 *ПРЕДСКАЗАНИЕ МАТЧА*",
            "",
            f"🟢 *Свет:* {', '.join(pred.radiant.heroes)}",
            f"🔴 *Тьма:* {', '.join(pred.dire.heroes)}",
            "",
            f"🏆 *Победитель:* {pred.get_winner_text()}",
            "",
            f"📊 *Уверенность:* {pred.get_confidence_text()} ({pred.confidence:.1f}%)",
            "",
            "*Факторы:*"
        ]
        
        for f in pred.key_factors[:3]:
            lines.append(f"• {f}")
        
        if pred.risk_factors:
            lines.extend(["", "*⚠️ Риски:*"])
            for r in pred.risk_factors[:2]:
                lines.append(f"• {r}")
        
        lines.append("")
        lines.append("_Анализ: синергии, контрпики, мета_")
        
        return "\n".join(lines)
    
    async def show_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data.split(":")
        if len(data) < 3:
            return
        
        radiant = data[1].split(",")
        dire = data[2].split(",")
        
        predictor = MatchPredictor()
        pred = await predictor.predict(radiant, dire)
        
        lines = [
            f"📊 *Детали: {pred.radiant.team_name} vs {pred.dire.team_name}*",
            "",
            f"*🟢 Свет ({pred.win_probability_radiant:.1f}%)*",
            f"Синергия: {pred.radiant.synergy_score:.0f}/100",
            f"Драфт: {pred.radiant.draft_score:.0f}/100",
            f"Мета: {pred.radiant.meta_score:.0f}/100",
        ]
        
        if pred.radiant.strengths:
            lines.append("\n*Сильные стороны:*")
            for s in pred.radiant.strengths[:3]:
                lines.append(f"  {s}")
        
        if pred.radiant.weaknesses:
            lines.append("\n*Слабости:*")
            for w in pred.radiant.weaknesses[:3]:
                lines.append(f"  {w}")
        
        lines.extend([
            "",
            f"*🔴 Тьма ({pred.win_probability_dire:.1f}%)*",
            f"Синергия: {pred.dire.synergy_score:.0f}/100",
            f"Драфт: {pred.dire.draft_score:.0f}/100",
            f"Мета: {pred.dire.meta_score:.0f}/100",
        ])
        
        if pred.dire.strengths:
            lines.append("\n*Сильные стороны:*")
            for s in pred.dire.strengths[:3]:
                lines.append(f"  {s}")
        
        if pred.dire.weaknesses:
            lines.append("\n*Слабости:*")
            for w in pred.dire.weaknesses[:3]:
                lines.append(f"  {w}")
        
        if pred.counter_matchups:
            lines.extend(["", "*🎯 Матчапы:*"])
            for m in pred.counter_matchups[:4]:
                lines.append(f"  {m['text']}")
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data=f"back:{','.join(radiant)}:{','.join(dire)}")
        ]])
        
        await query.edit_message_text("\n".join(lines), parse_mode='Markdown', reply_markup=keyboard)

class StatsHandlers:
    @staticmethod
    async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📊 Статистика из API в разработке. Используй `/hero [имя]` для базовой инфо.")
    
    @staticmethod
    async def meta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        heroes = HeroService.get_all_heroes()
        top = sorted(heroes, key=lambda h: h.stats.tier if h.stats else "Z")[:5]
        
        lines = ["🌍 *Текущая мета (по тирам):*\n"]
        for h in top:
            tier_emoji = {"S": "🔴", "A": "🟠", "B": "🟡", "C": "🟢", "D": "⚪"}.get(h.stats.tier if h.stats else "?", "❓")
            lines.append(f"{tier_emoji} *{h.name}* — {h.roles[0]}")
        
        await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
    
    @staticmethod
    async def counters_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Укажи имя героя: `/counters kez`")
            return
        
        hero_name = " ".join(context.args)
        hero = HeroService.find_hero(hero_name)
        
        if not hero:
            await update.message.reply_text(f"❌ Герой не найден")
            return
        
        # Показываем из базы
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
            
            elif data.startswith("details:"):
                await PredictionHandlers().show_details(update, context)
            
            elif data.startswith("back:"):
                parts = data.split(":")
                if len(parts) >= 3:
                    radiant = parts[1].split(",")
                    dire = parts[2].split(",")
                    await PredictionHandlers()._make_prediction(update, radiant, dire)
            
            elif data == "predict_new":
                await query.edit_message_text("🔮 Введи: `/predict [свет] vs [тьма]`", parse_mode='Markdown')
            
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
        
        except Exception as e:
            logger.error(f"Callback error: {e}")
            await query.edit_message_text("❌ Ошибка")

class ErrorHandlers:
    @staticmethod
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже или используйте /help"
            )

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
    logger.info("Dota 2 Counter Bot v2.0")
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
        
        # Keep alive
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
