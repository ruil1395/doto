import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from src.models.hero import Hero
from src.services.hero_service import HeroService


@dataclass
class FeatureVector:
    avg_win_rate_radiant: float
    avg_win_rate_dire: float
    win_rate_diff: float
    counter_score: float
    synergy_score: float
    has_carry: int
    has_mid: int
    has_offlane: int
    has_support: int
    physical_damage: float
    magical_damage: float
    pure_damage: float
    disable_score: float
    silence_score: float
    burst_score: float
    late_game_score: float
    push_score: float
    teamfight_score: float


class FeatureExtractor:
    ROLE_WEIGHTS = {
        "Carry": 1.5,
        "Mid": 1.3,
        "Offlane": 1.2,
        "Support": 1.0,
        "Hard Support": 0.9
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
    
    ANTISYNERGIES = {
        ("anti_mage", "medusa"): -10,
        ("invoker", "meepo"): -8,
        ("techies", "fast_game"): -15,
    }
    
    @staticmethod
    def _get_hero(hero_name: str) -> Optional[Hero]:
        return HeroService.find_hero(hero_name)
    
    @staticmethod
    def extract(heroes: List[str]) -> Dict[str, float]:
        features = {
            "count": len(heroes),
            "avg_tier": 0,
            "has_initiator": 0,
            "has_carry": 0,
            "has_control": 0,
            "has_heal": 0,
            "has_push": 0,
            "melee_count": 0,
            "ranged_count": 0,
        }
        
        if not heroes:
            return features
            
        total_tier_score = 0
        
        for hero_name in heroes:
            hero = FeatureExtractor._get_hero(hero_name)
            if not hero:
                continue
                
            roles = [r.lower() for r in hero.roles]
            
            if any(r in roles for r in ["carry", "nuker"]):
                features["has_carry"] = 1
            if any(r in roles for r in ["initiator", "disabler"]):
                features["has_initiator"] = 1
            if any(r in roles for r in ["support", "healer"]):
                features["has_heal"] = 1
            if "pusher" in roles:
                features["has_push"] = 1
                
            if hero.attack_type == "Melee":
                features["melee_count"] += 1
            else:
                features["ranged_count"] += 1
                
            tier_map = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
            tier_score = tier_map.get(hero.stats.tier if hero.stats else "C", 3)
            total_tier_score += tier_score
            
        features["avg_tier"] = total_tier_score / len(heroes) if heroes else 0
        
        return features
    
    @staticmethod
    def calculate_synergy(heroes: List[str]) -> float:
        if len(heroes) < 2:
            return 50.0
            
        synergy_score = 50.0
        hero_ids = [h.lower().replace(" ", "_") for h in heroes]
        
        for (h1, h2), bonus in FeatureExtractor.SYNERGIES.items():
            if h1 in hero_ids and h2 in hero_ids:
                synergy_score += bonus
            elif h2 in hero_ids and h1 in hero_ids:
                synergy_score += bonus
                
        for (h1, h2), penalty in FeatureExtractor.ANTISYNERGIES.items():
            if h1 in hero_ids and h2 in hero_ids:
                synergy_score += penalty
                
        features = FeatureExtractor.extract(heroes)
        if features["has_carry"] and features["has_initiator"] and features["has_heal"]:
            synergy_score += 10
            
        if not features["has_carry"]:
            synergy_score -= 20
        if not features["has_initiator"]:
            synergy_score -= 15
            
        return max(0, min(100, synergy_score))
    
    @staticmethod
    def calculate_counter_score(team1: List[str], team2: List[str]) -> float:
        if not team1 or not team2:
            return 50.0
            
        total_advantage = 0
        matchups_count = 0
        
        for hero1 in team1:
            h1 = FeatureExtractor._get_hero(hero1)
            if not h1:
                continue
                
            for hero2 in team2:
                if hero2.lower() in [h.lower() for h in h1.counters.weak_against]:
                    total_advantage -= 10
                    matchups_count += 1
                    
                h2 = FeatureExtractor._get_hero(hero2)
                if h2 and hero1.lower() in [h.lower() for h in h2.counters.weak_against]:
                    total_advantage += 10
                    matchups_count += 1
                    
        if matchups_count == 0:
            return 50.0
            
        avg_advantage = total_advantage / matchups_count
        return max(0, min(100, 50 + avg_advantage))
    
    @staticmethod
    def create_feature_vector(radiant: List[str], dire: List[str]) -> FeatureVector:
        rad_features = FeatureExtractor.extract(radiant)
        dire_features = FeatureExtractor.extract(dire)
        
        rad_synergy = FeatureExtractor.calculate_synergy(radiant)
        dire_synergy = FeatureExtractor.calculate_synergy(dire)
        
        rad_counter = FeatureExtractor.calculate_counter_score(radiant, dire)
        dire_counter = FeatureExtractor.calculate_counter_score(dire, radiant)
        
        has_carry = 1 if (rad_features["has_carry"] and dire_features["has_carry"]) else 0
        
        return FeatureVector(
            avg_win_rate_radiant=rad_features["avg_tier"] * 20,
            avg_win_rate_dire=dire_features["avg_tier"] * 20,
            win_rate_diff=(rad_features["avg_tier"] - dire_features["avg_tier"]) * 5,
            counter_score=rad_counter,
            synergy_score=rad_synergy - dire_synergy,
            has_carry=has_carry,
            has_mid=1,
            has_offlane=1,
            has_support=1,
            physical_damage=50,
            magical_damage=50,
            pure_damage=10,
            disable_score=rad_features["has_initiator"] * 30,
            silence_score=0,
            burst_score=rad_features["has_carry"] * 25,
            late_game_score=50,
            push_score=(rad_features["has_push"] - dire_features["has_push"]) * 10,
            teamfight_score=(rad_synergy - 50) / 2
        )
