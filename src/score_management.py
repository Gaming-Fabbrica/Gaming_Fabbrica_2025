import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from src.enums import MonsterType

class ScoreManager:
    def __init__(self, leaderboard_file: str = 'src/assets/leaderboard.json'):
        """
        Initialise le gestionnaire de scores
        
        Args:
            leaderboard_file: Chemin vers le fichier de leaderboard
        """
        self.leaderboard_file = leaderboard_file
        self.leaderboard = self.load_leaderboard()
        
    def reset(self) -> None:
        """
        Réinitialise le gestionnaire de scores, rechargeant le leaderboard depuis le fichier
        """
        self.leaderboard = self.load_leaderboard()
        
    def load_leaderboard(self) -> List[Dict]:
        """
        Charge le leaderboard depuis le fichier
        
        Returns:
            Liste des scores du leaderboard
        """
        if not os.path.exists(self.leaderboard_file):
            # Créer le dossier si nécessaire
            os.makedirs(os.path.dirname(self.leaderboard_file), exist_ok=True)
            # Créer un leaderboard vide
            return []
        
        try:
            with open(self.leaderboard_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement du leaderboard: {e}")
            return []
    
    def save_leaderboard(self) -> bool:
        """
        Sauvegarde le leaderboard dans le fichier
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            # Créer le dossier si nécessaire
            os.makedirs(os.path.dirname(self.leaderboard_file), exist_ok=True)
            
            with open(self.leaderboard_file, 'w') as f:
                json.dump(self.leaderboard, f, indent=2)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du leaderboard: {e}")
            return False
    
    def add_score(self, player_name: str, score: int, survived_time: float, waves_completed: int) -> bool:
        """
        Ajoute un score au leaderboard
        
        Args:
            player_name: Nom du joueur
            score: Score obtenu
            survived_time: Temps de survie en secondes
            waves_completed: Nombre de vagues complétées
            
        Returns:
            True si l'ajout a réussi, False sinon
        """
        # Créer l'entrée de score
        score_entry = {
            "player_name": player_name,
            "score": score,
            "survived_time": survived_time,
            "waves_completed": waves_completed,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Ajouter au leaderboard
        self.leaderboard.append(score_entry)
        
        # Trier le leaderboard par score décroissant
        self.leaderboard.sort(key=lambda x: x["score"], reverse=True)
        
        # Limiter à 10 entrées maximum
        if len(self.leaderboard) > 10:
            self.leaderboard = self.leaderboard[:10]
        
        # Sauvegarder le leaderboard
        return self.save_leaderboard()
    
    def get_leaderboard(self) -> List[Dict]:
        """
        Récupère le leaderboard
        
        Returns:
            Liste des scores du leaderboard
        """
        return self.leaderboard
    
    def get_current_player_rank(self, score: int) -> Optional[int]:
        """
        Détermine le rang potentiel d'un score dans le leaderboard
        
        Args:
            score: Score à évaluer
            
        Returns:
            Rang potentiel (1-based) ou None si le score n'entre pas dans le top 10
        """
        # Si le leaderboard est vide ou contient moins de 10 entrées, le score est éligible
        if len(self.leaderboard) < 10:
            # Trouver sa position
            rank = 1
            for entry in self.leaderboard:
                if score < entry["score"]:
                    rank += 1
            return rank
        
        # Si le score est meilleur que le dernier du leaderboard
        if score > self.leaderboard[-1]["score"]:
            # Trouver sa position
            rank = 1
            for entry in self.leaderboard:
                if score < entry["score"]:
                    rank += 1
            return rank
        
        return None  # Le score n'est pas éligible pour le leaderboard
    
    def is_high_score(self, score: int) -> bool:
        """
        Vérifie si un score est un high score (top 10)
        
        Args:
            score: Score à vérifier
            
        Returns:
            True si le score est un high score, False sinon
        """
        return self.get_current_player_rank(score) is not None
    
    def format_time(self, seconds: float) -> str:
        """
        Formate un temps en secondes en format mm:ss
        
        Args:
            seconds: Temps en secondes
            
        Returns:
            Temps formaté
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def get_monster_score_value(self, monster_type: MonsterType) -> int:
        """
        Retourne la valeur en points du monstre selon son type
        
        Args:
            monster_type: Type de monstre
            
        Returns:
            Valeur en points du monstre
        """
        score_values = {
            MonsterType.SKELETON: 10,
            MonsterType.WOLF: 15,
            MonsterType.MORAY: 20,
            MonsterType.SMALL_SPIRIT: 25,
            MonsterType.FIRE_SKELETON: 30,
            MonsterType.WITCH: 40,
            MonsterType.KAMIKAZE: 35,
            MonsterType.GIANT_WOLF: 50,
            MonsterType.GIANT_SKELETON: 45,
            MonsterType.ROYAL_MORAY: 60,
            MonsterType.DRAGON: 100
        }
        # Valeur par défaut si le type n'est pas dans le dictionnaire
        return score_values.get(monster_type, 10) 