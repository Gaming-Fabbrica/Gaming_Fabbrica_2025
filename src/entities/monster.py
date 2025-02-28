import pygame
import math
import random
from dataclasses import dataclass
from ..constants import (
    MONSTER_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT, LIGHT_RADIUS,
    MAX_FLEE_TIME, MONSTER_FEAR_DURATION, DEBUG_LINE_ALPHA,
    HEAL_RANGE, SPIRIT_BUFF_RANGE, KAMIKAZE_EXPLOSION_RANGE,
    TOWER_SIZE, VILLAGE_SIZE, MAX_VISIBILITY_RANGE,
    FLEE_DISTANCE_MIN, FLEE_DISTANCE_MAX, FLEE_ANGLE_VARIATION,
    WORLD_SIZE
)
from ..enums import MonsterType, MONSTER_NAMES
from .projectile import Projectile

@dataclass
class WaveMonster:
    monster_type: MonsterType
    count: int
    spawn_delay: float  # Délai entre chaque monstre en secondes

class Monster:
    # Statistiques des monstres
    MONSTER_STATS = {
        MonsterType.SKELETON: {
            'max_health': 100,
            'max_damage': 10,
            'speed': 2,
            'shield': 0,
            'attack_speed': 1,
            'light_fear': 70,
            'color': (150, 150, 150),  # Gris
            'group_factor': 80,  # Apparaissent très groupés (en hordes)
        },
        MonsterType.WOLF: {
            'max_health': 150,
            'max_damage': 15,
            'speed': 3,
            'shield': 5,
            'attack_speed': 1.5,
            'light_fear': 60,
            'color': (139, 69, 19),  # Marron
            'group_factor': 70,  # Meutes de loups
        },
        MonsterType.MORAY: {
            'max_health': 200,
            'max_damage': 20,
            'speed': 2.5,
            'shield': 10,
            'attack_speed': 1.2,
            'light_fear': 50,
            'color': (0, 191, 255),  # Bleu clair
            'group_factor': 40,  # Plutôt solitaires
            'attack_range': 100,  # Distance de tir
            'projectile_speed': 300,
        },
        MonsterType.SMALL_SPIRIT: {
            'max_health': 80,
            'max_damage': 30,
            'speed': 4,
            'shield': 0,
            'attack_speed': 1,
            'light_fear': 90,
            'color': (220, 220, 255),  # Blanc bleuté
            'group_factor': 90,  # Très groupés (nuées d'esprits)
        },
        MonsterType.FIRE_SKELETON: {
            'max_health': 250,
            'max_damage': 25,
            'speed': 2,
            'shield': 15,
            'attack_speed': 1.3,
            'light_fear': 40,
            'color': (255, 69, 0),  # Orange feu
            'group_factor': 60,  # Groupes moyens
        },
        MonsterType.WITCH: {
            'max_health': 300,
            'max_damage': 20,
            'speed': 1.5,
            'shield': 20,
            'attack_speed': 2,
            'light_fear': 30,
            'color': (138, 43, 226),  # Violet
            'group_factor': 20,  # Très solitaires
        },
        MonsterType.KAMIKAZE: {
            'max_health': 100,
            'max_damage': 150,
            'speed': 5,
            'shield': 0,
            'attack_speed': 1,
            'light_fear': 20,
            'color': (255, 0, 0),  # Rouge vif
            'group_factor': 50,  # Groupes moyens
        },
        MonsterType.GIANT_WOLF: {
            'max_health': 400,
            'max_damage': 40,
            'speed': 2.5,
            'shield': 25,
            'attack_speed': 1.2,
            'light_fear': 25,
            'color': (101, 67, 33),  # Marron foncé
            'group_factor': 30,  # Petits groupes
        },
        MonsterType.GIANT_SKELETON: {
            'max_health': 500,
            'max_damage': 45,
            'speed': 1.5,
            'shield': 30,
            'attack_speed': 0.8,
            'light_fear': 20,
            'color': (169, 169, 169),  # Gris foncé
            'group_factor': 40,  # Groupes moyens
        },
        MonsterType.ROYAL_MORAY: {
            'max_health': 600,
            'max_damage': 50,
            'speed': 2,
            'shield': 35,
            'attack_speed': 1.5,
            'light_fear': 15,
            'color': (0, 0, 139),  # Bleu foncé
            'group_factor': 10,  # Très solitaire
        },
        MonsterType.DRAGON: {
            'max_health': 1000,
            'max_damage': 100,
            'speed': 3,
            'shield': 50,
            'attack_speed': 2,
            'light_fear': 5,
            'color': (178, 34, 34),  # Rouge foncé
            'group_factor': 5,  # Extrêmement solitaire
            'attack_range': 150,
            'projectile_speed': 400,
        }
    }

    def __init__(self, monster_type, x, y, initial_direction=0):
        self.monster_type = monster_type
        self.x = x
        self.y = y
        
        # Récupérer les stats de base pour ce type de monstre
        stats = self.MONSTER_STATS[monster_type]
        
        # Stats de base
        self.max_health = stats['max_health']
        self.current_health = self.max_health
        self.max_damage = stats['max_damage']
        self.current_damage = self.max_damage
        self.speed = stats['speed']
        self.shield = stats['shield']
        self.attack_speed = stats['attack_speed']
        self.light_fear = stats['light_fear']
        self.color = stats['color']
        self.direction = initial_direction
        self.target_direction = initial_direction
        self.rotation_speed = math.pi  # Vitesse de rotation en radians par seconde
        
        # États
        self.is_fleeing = False
        self.flee_time = 0
        self.flee_target_x = None
        self.flee_target_y = None
        self.target = None
        self.path = []
        self.group_factor = stats['group_factor']
        self.current_target = None
        self.current_target_type = None
        self.is_dead = False
        
        # Probabilité de cibler le village directement
        self.target_village_chance = 0.15 if monster_type in [MonsterType.KAMIKAZE, 
                                                            MonsterType.DRAGON] else 0.05
        
        # Capacités spéciales
        self.projectiles = []
        self.attack_cooldown = 0
        self.can_shoot = monster_type in [MonsterType.MORAY, MonsterType.DRAGON]
        if self.can_shoot:
            self.attack_range = stats['attack_range']
            self.projectile_speed = stats['projectile_speed']

        # Zones d'effet spéciales selon le type
        if monster_type == MonsterType.WITCH:
            self.effect_range = HEAL_RANGE
            self.effect_color = (138, 43, 226, 128)  # Violet transparent
        elif monster_type == MonsterType.SMALL_SPIRIT:
            self.effect_range = SPIRIT_BUFF_RANGE
            self.effect_color = (220, 220, 255, 128)  # Blanc bleuté transparent
        elif monster_type == MonsterType.KAMIKAZE:
            self.effect_range = KAMIKAZE_EXPLOSION_RANGE
            self.effect_color = (255, 0, 0, 128)  # Rouge transparent
        
        if self.can_shoot:
            self.effect_range = stats['attack_range']
            self.effect_color = (*self.color, 128)

    def take_damage(self, amount):
        """Applique les dégâts en tenant compte du bouclier"""
        actual_damage = max(0, amount - self.shield)
        self.current_health -= actual_damage
        if self.current_health <= 0:
            self.is_dead = True
            return True
        return False

    def heal(self, amount):
        """Soigne le monstre sans dépasser sa vie maximale"""
        self.current_health = min(self.max_health, self.current_health + amount)
        
    def boost_damage(self, amount):
        """Augmente les dégâts sans dépasser le maximum"""
        self.current_damage = min(self.max_damage, self.current_damage + amount)

    def check_light_fear(self, light_intensity):
        """Vérifie si le monstre doit fuir la lumière"""
        if light_intensity * (self.light_fear / 100) > 0.5:
            self.is_fleeing = True
            return True
        self.is_fleeing = False
        return False

    def start_fleeing(self, light_position):
        """Démarre la fuite du monstre"""
        if self.current_target:
            target_x = self.current_target.x if self.current_target_type == 'tower' else self.village_x
            target_y = self.current_target.y if self.current_target_type == 'tower' else self.village_y
            
            dx = self.x - target_x
            dy = self.y - target_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            self.flee_target_x = self.x + dx
            self.flee_target_y = self.y + dy
            
            # Limiter la position cible dans les limites du monde
            self.flee_target_x = max(0, min(self.flee_target_x, WORLD_SIZE))
            self.flee_target_y = max(0, min(self.flee_target_y, WORLD_SIZE))
            
            fear_factor = self.MONSTER_STATS[self.monster_type]['light_fear'] / 100.0
            self.flee_time = MAX_FLEE_TIME * fear_factor
            
            self.is_fleeing = True
            self.current_target = None
            self.current_target_type = None

    def update(self, towers, village_x, village_y, delta_time, light_position=None, light_active=False, light_power=0):
        """Met à jour l'état du monstre"""
        if self.is_fleeing:
            self.update_fleeing(delta_time)
            return

        # Gestion de la lumière
        if light_active and light_position and light_power > 0:
            dist_to_light = math.sqrt((light_position[0] - self.x)**2 + 
                                    (light_position[1] - self.y)**2)
            if dist_to_light < LIGHT_RADIUS:
                if random.random() * 100 < self.MONSTER_STATS[self.monster_type]['light_fear']:
                    self.start_fleeing(light_position)
                    return

        # Comportement normal
        self.update_normal_behavior(towers, village_x, village_y, delta_time)

    def update_fleeing(self, delta_time):
        """Met à jour le comportement de fuite"""
        self.flee_time -= delta_time
        if self.flee_time <= 0:
            self.is_fleeing = False
            self.flee_target_x = None
            self.flee_target_y = None
            self.current_target = None
            self.current_target_type = None
            return

        dx = self.flee_target_x - self.x
        dy = self.flee_target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 5:
            self.move_towards_target(dx, dy, distance, delta_time, flee_multiplier=2)

    def update_normal_behavior(self, towers, village_x, village_y, delta_time):
        """Met à jour le comportement normal du monstre"""
        if not self.current_target or \
           (self.current_target_type == 'tower' and self.current_target not in towers):
            self.choose_new_target(towers, village_x, village_y)

        target_x = self.current_target.x if self.current_target_type == 'tower' else village_x
        target_y = self.current_target.y if self.current_target_type == 'tower' else village_y
        
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 5:
            self.move_towards_target(dx, dy, distance, delta_time)
            
        self.handle_attack(distance, delta_time)

    def move_towards_target(self, dx, dy, distance, delta_time, flee_multiplier=1):
        """Déplace le monstre vers sa cible"""
        self.target_direction = math.atan2(dy, dx)
        
        angle_diff = (self.target_direction - self.direction + math.pi) % (2 * math.pi) - math.pi
        max_rotation = self.rotation_speed * delta_time
        
        if abs(angle_diff) > max_rotation:
            self.direction += max_rotation if angle_diff > 0 else -max_rotation
        else:
            self.direction = self.target_direction
        
        move_speed = self.speed * flee_multiplier * delta_time
        self.x += math.cos(self.direction) * move_speed
        self.y += math.sin(self.direction) * move_speed

    def handle_attack(self, distance, delta_time):
        """Gère l'attaque du monstre"""
        if self.current_target_type == 'tower' and distance < TOWER_SIZE:
            if self.current_target.take_damage(self.current_damage * delta_time * self.attack_speed):
                self.current_target = None
                self.current_target_type = None

    def choose_new_target(self, towers, village_x, village_y):
        """Choisit une nouvelle cible pour le monstre"""
        if random.random() < self.target_village_chance:
            self.current_target_type = 'village'
            self.current_target = None
        else:
            closest_tower = None
            closest_dist = float('inf')
            for tower in towers:
                dist = math.sqrt((tower.x - self.x)**2 + (tower.y - self.y)**2)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_tower = tower
            if closest_tower:
                self.current_target_type = 'tower'
                self.current_target = closest_tower
            else:
                self.current_target_type = 'village'
                self.current_target = None

    def draw(self, screen, camera_x, camera_y, zoom, show_names=False, show_monster_ranges=False):
        """Dessine le monstre et ses effets"""
        screen_x, screen_y = self.world_to_screen(camera_x, camera_y, zoom)
        
        # Dessiner le triangle du monstre
        points = self.calculate_triangle_points(screen_x, screen_y, zoom)
        pygame.draw.polygon(screen, self.color, points)
        
        # Dessiner la barre de vie
        self.draw_health_bar(screen, screen_x, screen_y, zoom)
        
        # Afficher le nom si activé
        if show_names:
            self.draw_name(screen, screen_x, screen_y, zoom)
        
        # Afficher les zones d'effet si activé
        if show_monster_ranges:
            self.draw_effect_range(screen, screen_x, screen_y, zoom)

    def calculate_triangle_points(self, screen_x, screen_y, zoom):
        """Calcule les points du triangle représentant le monstre"""
        angle = math.pi / 4  # 45 degrés pour la largeur du triangle
        size = MONSTER_SIZE * zoom
        
        front_x = screen_x + math.cos(self.direction) * size
        front_y = screen_y + math.sin(self.direction) * size
        
        back_left_x = screen_x + math.cos(self.direction + math.pi - angle) * size
        back_left_y = screen_y + math.sin(self.direction + math.pi - angle) * size
        
        back_right_x = screen_x + math.cos(self.direction + math.pi + angle) * size
        back_right_y = screen_y + math.sin(self.direction + math.pi + angle) * size
        
        return [(front_x, front_y), 
                (back_left_x, back_left_y), 
                (back_right_x, back_right_y)]

    def draw_health_bar(self, screen, screen_x, screen_y, zoom):
        """Dessine la barre de vie du monstre"""
        health_ratio = self.current_health / self.max_health
        health_width = MONSTER_SIZE * zoom
        health_height = 3 * zoom
        health_x = screen_x - health_width/2
        health_y = screen_y - MONSTER_SIZE * zoom - health_height - 2
        
        pygame.draw.rect(screen, (64, 64, 64),
                        (health_x, health_y, health_width, health_height))
        health_color = (0, 255, 0) if health_ratio > 0.5 else \
                      (255, 255, 0) if health_ratio > 0.25 else \
                      (255, 0, 0)
        pygame.draw.rect(screen, health_color,
                        (health_x, health_y, health_width * health_ratio, health_height))

    def draw_name(self, screen, screen_x, screen_y, zoom):
        """Affiche le nom du monstre"""
        font = pygame.font.Font(None, int(20 * zoom))
        name_surface = font.render(MONSTER_NAMES[self.monster_type], True, self.color)
        name_x = screen_x - name_surface.get_width()/2
        name_y = screen_y - MONSTER_SIZE * zoom - 20 * zoom
        screen.blit(name_surface, (name_x, name_y))

    def draw_effect_range(self, screen, screen_x, screen_y, zoom):
        """Dessine la zone d'effet du monstre si applicable"""
        if hasattr(self, 'effect_range'):
            range_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            radius = int(self.effect_range * zoom)
            pygame.draw.circle(range_surface, self.effect_color,
                             (int(screen_x), int(screen_y)), radius)
            screen.blit(range_surface, (0, 0))

    def world_to_screen(self, camera_x, camera_y, zoom):
        """Convertit les coordonnées du monde en coordonnées écran"""
        screen_x = (self.x - camera_x) * zoom + WINDOW_WIDTH/2
        screen_y = (self.y - camera_y) * zoom + WINDOW_HEIGHT/2
        return screen_x, screen_y 

    def is_visible(self, village_x, village_y, towers):
        """Vérifie si le monstre est visible depuis le village ou une tour"""
        # Vérifier la distance par rapport au village
        dist_to_village = math.sqrt((self.x - village_x)**2 + (self.y - village_y)**2)
        if dist_to_village <= MAX_VISIBILITY_RANGE:
            return True
            
        # Vérifier la distance par rapport aux tours
        for tower in towers:
            dist_to_tower = math.sqrt((self.x - tower.x)**2 + (self.y - tower.y)**2)
            if dist_to_tower <= tower.vision_range:
                return True
                
        return False 