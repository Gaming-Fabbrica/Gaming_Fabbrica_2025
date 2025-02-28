import random
import math
from dataclasses import dataclass
from typing import List
from ..constants import (
    MIN_SPAWN_DISTANCE, MAX_SPAWN_DISTANCE, WORLD_SIZE
)
from ..enums import MonsterType
from ..entities.monster import Monster, WaveMonster

@dataclass
class Wave:
    monsters: List[WaveMonster]
    spawn_distance: float  # Distance de spawn du village
    wave_delay: float     # Délai avant la prochaine vague en secondes

class WaveManager:
    def __init__(self, village_x, village_y, game):
        self.village_x = village_x
        self.village_y = village_y
        self.game = game  # Référence au jeu
        self.current_wave = 0
        self.wave_started = False
        self.last_spawn_time = 0
        self.current_monster_index = 0
        self.monsters_to_spawn = []
        self.next_wave_time = 0
        
        # Définition des vagues
        self.waves = [
            # Vague 1: Squelettes et loups
            Wave(
                monsters=[
                    WaveMonster(MonsterType.SKELETON, count=5, spawn_delay=1.0),
                    WaveMonster(MonsterType.WOLF, count=3, spawn_delay=2.0)
                ],
                spawn_distance=MIN_SPAWN_DISTANCE,
                wave_delay=10.0
            ),
            # Vague 2: Murènes et esprits
            Wave(
                monsters=[
                    WaveMonster(MonsterType.MORAY, count=3, spawn_delay=2.0),
                    WaveMonster(MonsterType.SMALL_SPIRIT, count=4, spawn_delay=1.5)
                ],
                spawn_distance=MIN_SPAWN_DISTANCE + 100,
                wave_delay=15.0
            ),
            # Vague 3: Mix plus difficile
            Wave(
                monsters=[
                    WaveMonster(MonsterType.FIRE_SKELETON, count=2, spawn_delay=3.0),
                    WaveMonster(MonsterType.WITCH, count=1, spawn_delay=0),
                    WaveMonster(MonsterType.KAMIKAZE, count=3, spawn_delay=1.0)
                ],
                spawn_distance=MAX_SPAWN_DISTANCE - 100,
                wave_delay=20.0
            ),
            # Vague finale: Boss
            Wave(
                monsters=[
                    WaveMonster(MonsterType.DRAGON, count=1, spawn_delay=0),
                    WaveMonster(MonsterType.GIANT_SKELETON, count=2, spawn_delay=5.0)
                ],
                spawn_distance=MAX_SPAWN_DISTANCE,
                wave_delay=0  # Dernière vague
            )
        ]

    def get_spawn_position(self, distance, group_factor):
        """Calcule une position de spawn en tenant compte du facteur de groupe"""
        base_angle = random.uniform(0, 2 * math.pi)
        
        # Ajuster l'angle en fonction du facteur de groupe
        angle_variation = (1 - group_factor/100) * math.pi  # Plus le group_factor est élevé, plus l'angle varie peu
        angle = base_angle + random.uniform(-angle_variation, angle_variation)
        
        # Calculer la position
        x = self.village_x + math.cos(angle) * distance
        y = self.village_y + math.sin(angle) * distance
        
        # S'assurer que la position est dans les limites du monde
        x = max(0, min(x, WORLD_SIZE))
        y = max(0, min(y, WORLD_SIZE))
        
        return x, y, angle

    def update(self, current_time):
        """Met à jour la gestion des vagues"""
        if self.current_wave >= len(self.waves):
            return None  # Plus de vagues
            
        if not self.wave_started:
            if current_time >= self.next_wave_time:
                self.wave_started = True
                self.prepare_next_wave()
            return None
            
        if current_time - self.last_spawn_time >= self.monsters_to_spawn[0][1]:
            monster_type, _, group_factor = self.monsters_to_spawn.pop(0)
            x, y, angle = self.get_spawn_position(
                self.waves[self.current_wave].spawn_distance,
                group_factor
            )
            
            self.last_spawn_time = current_time
            
            if not self.monsters_to_spawn:  # Fin de la vague
                self.wave_started = False
                self.current_wave += 1
                self.next_wave_time = current_time + self.waves[self.current_wave-1].wave_delay
                
            return Monster(monster_type, x, y, self.game)
            
        return None

    def prepare_next_wave(self):
        """Prépare la liste des monstres à spawner pour la prochaine vague"""
        self.monsters_to_spawn = []
        wave = self.waves[self.current_wave]
        
        for wave_monster in wave.monsters:
            for _ in range(wave_monster.count):
                group_factor = Monster.MONSTER_STATS[wave_monster.monster_type]['group_factor']
                self.monsters_to_spawn.append((
                    wave_monster.monster_type,
                    wave_monster.spawn_delay,
                    group_factor
                )) 

    def generate_monster(self, monster_type, x, y):
        """Crée un nouveau monstre"""
        return Monster(monster_type, x, y, self.game)  # Passer la référence au jeu 