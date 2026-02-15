import math
import random
from typing import List, Dict, Tuple, Optional

from src.models.prediction import MatchPrediction, TeamAnalysis, PredictionResult
from src.ml.features import FeatureExtractor, FeatureVector


class MatchPredictor:
    WEIGHTS = {
        "win_rate": 0.25,
        "synergy": 0.20,
        "counter": 0.25,
        "draft": 0.15,
        "meta": 0.15
    }
    
    async def predict(self, radiant: List[str], dire: List[str]) -> MatchPrediction:
        radiant_analysis = await self._analyze_team(radiant, "Radiant")
        dire_analysis = await self._analyze_team(dire, "Dire")
        
        lane_matchups = self._analyze_lane_matchups(radiant, dire)
        counter_matchups = self._analyze_counter_matchups(radiant, dire)
        
        features = FeatureExtractor.create_feature_vector(radiant, dire)
        
        rad_prob, dire_prob = self._calculate_probabilities(
            features, radiant_analysis, dire_analysis
        )
        
        result, confidence = self._determine_result(rad_prob, dire_prob)
        
        key_factors = self._extract_key_factors(
            features, radiant_analysis, dire_analysis, rad_prob, dire_prob
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
            lane_matchups=lane_matchups,
            counter_matchups=counter_matchups
        )
    
    async def _analyze_team(self, heroes: List[str], team_name: str) -> TeamAnalysis:
        synergy = FeatureExtractor.calculate_synergy(heroes)
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
    
    def _evaluate_draft(self, heroes: List[str]) -> float:
        score = 50.0
        features = FeatureExtractor.extract(heroes)
        
        if features["has_carry"] and features["has_initiator"]:
            score += 15
        if features["melee_count"] > 0 and features["ranged_count"] > 0:
            score += 10
        if features["has_heal"]:
            score += 10
        if features["has_push"]:
            score += 5
        if features["count"] < 5:
            score -= (5 - features["count"]) * 10
            
        return max(0, min(100, score))
    
    def _evaluate_meta_score(self, heroes: List[str]) -> float:
        if not heroes:
            return 0
            
        total_score = 0
        
        for hero_name in heroes:
            hero = FeatureExtractor._get_hero(hero_name)
            if hero and hero.stats:
                tier_score = {"S": 100, "A": 85, "B": 70, "C": 55, "D": 40}.get(hero.stats.tier, 50)
                total_score += tier_score
            else:
                total_score += 50
                
        return total_score / len(heroes) if heroes else 0
    
    def _analyze_strengths_weaknesses(self, heroes: List[str]) -> Tuple[List[str], List[str]]:
        strengths = []
        weaknesses = []
        
        features = FeatureExtractor.extract(heroes)
        
        if features["has_carry"] and features["has_initiator"]:
            strengths.append("Сбалансированный состав с керри и инициатором")
        if features["has_heal"]:
            strengths.append("Есть sustain в команде")
        if features["has_push"]:
            strengths.append("Сильный пуш потенциал")
        if features["melee_count"] >= 3:
            strengths.append("Много melee для teamfight")
            
        if not features["has_carry"]:
            weaknesses.append("❌ Нет явного керри (поздняя игра сложна)")
        if not features["has_initiator"]:
            weaknesses.append("❌ Нет инициатора (сложно начинать файты)")
        if not features["has_heal"]:
            weaknesses.append("⚠️ Нет хила (зависимость от регена)")
        if features["ranged_count"] == 0:
            weaknesses.append("⚠️ Все melee (проблемы на линии)")
            
        return strengths, weaknesses
    
    def _identify_key_heroes(self, heroes: List[str]) -> List[str]:
        key_heroes = []
        
        for hero_name in heroes:
            hero = FeatureExtractor._get_hero(hero_name)
            if not hero:
                continue
                
            roles = [r.lower() for r in hero.roles]
            
            if "carry" in roles:
                key_heroes.append(f"{hero.name} (Керри)")
            elif "initiator" in roles:
                key_heroes.append(f"{hero.name} (Инициатор)")
                
            if hero.name in ["Magnus", "Dark Seer", "Enigma"]:
                key_heroes.append(f"{hero.name} (Teamfight)")
                
        return key_heroes[:3]
    
    def _analyze_lane_matchups(self, radiant: List[str], dire: List[str]) -> List[Dict]:
        matchups = []
        
        if len(radiant) >= 3 and len(dire) >= 3:
            matchups.append({
                "lane": "Мид",
                "radiant": radiant[1] if len(radiant) > 1 else radiant[0],
                "dire": dire[1] if len(dire) > 1 else dire[0],
                "advantage": "Зависит от механики"
            })
            
        return matchups
    
    def _analyze_counter_matchups(self, radiant: List[str], dire: List[str]) -> List[Dict]:
        matchups = []
        
        for rad_hero in radiant:
            for dire_hero in dire:
                rad = FeatureExtractor._get_hero(rad_hero)
                dire_h = FeatureExtractor._get_hero(dire_hero)
                
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
    
    def _calculate_probabilities(
        self, 
        features: FeatureVector,
        radiant: TeamAnalysis,
        dire: TeamAnalysis
    ) -> Tuple[float, float]:
        
        rad_score = (
            radiant.synergy_score * self.WEIGHTS["synergy"] +
            radiant.draft_score * self.WEIGHTS["draft"] +
            radiant.meta_score * self.WEIGHTS["meta"]
        )
        
        dire_score = (
            dire.synergy_score * self.WEIGHTS["synergy"] +
            dire.draft_score * self.WEIGHTS["draft"] +
            dire.meta_score * self.WEIGHTS["meta"]
        )
        
        counter_bonus = (features.counter_score - 50) * self.WEIGHTS["counter"]
        rad_score += counter_bonus
        dire_score -= counter_bonus
        
        total = rad_score + dire_score
        if total == 0:
            return 50.0, 50.0
            
        rad_prob = (rad_score / total) * 100
        dire_prob = 100 - rad_prob
        
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
    
    def _extract_key_factors(
        self,
        features: FeatureVector,
        radiant: TeamAnalysis,
        dire: TeamAnalysis,
        rad_prob: float,
        dire_prob: float
    ) -> List[str]:
        factors = []
        
        if radiant.synergy_score > dire.synergy_score + 10:
            factors.append(f"🤝 Лучшая синергия у Света (+{radiant.synergy_score - dire.synergy_score:.0f})")
        elif dire.synergy_score > radiant.synergy_score + 10:
            factors.append(f"🤝 Лучшая синергия у Тьмы (+{dire.synergy_score - radiant.synergy_score:.0f})")
            
        if features.counter_score > 60:
            factors.append(f"🎯 Свет имеет преимущество в матчапах ({features.counter_score:.0f}%)")
        elif features.counter_score < 40:
            factors.append(f"🎯 Тьма имеет преимущество в матчапах ({100-features.counter_score:.0f}%)")
            
        if radiant.meta_score > dire.meta_score + 10:
            factors.append("📈 Пик Света сильнее в текущей мете")
        elif dire.meta_score > radiant.meta_score + 10:
            factors.append("📈 Пик Тьмы сильнее в текущей мете")
            
        if radiant.draft_score > 80 and dire.draft_score < 60:
            factors.append("✅ Состав Света более сбалансирован")
        elif dire.draft_score > 80 and radiant.draft_score < 60:
            factors.append("✅ Состав Тьмы более сбалансирован")
            
        return factors[:4]
    
    def _extract_risks(self, radiant: TeamAnalysis, dire: TeamAnalysis) -> List[str]:
        risks = []
        
        if not radiant.strengths:
            risks.append("⚠️ У Света нет явных сильных сторон")
        if not dire.strengths:
            risks.append("⚠️ У Тьмы нет явных сильных сторон")
            
        if len(radiant.heroes) < 5:
            risks.append(f"⚠️ Состав Света неполный ({len(radiant.heroes)}/5)")
        if len(dire.heroes) < 5:
            risks.append(f"⚠️ Состав Тьмы неполный ({len(dire.heroes)}/5)")
            
        return risks
