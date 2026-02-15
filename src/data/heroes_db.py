from src.models.hero import Hero, HeroCounters, HeroBuild, HeroStats

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
