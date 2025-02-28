import pygame
import sys
from enum import Enum, auto
import json
import os
import math
import random
from dataclasses import dataclass
from typing import List, Dict
import time

# Constantes
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
GRID_SIZE = 32
FPS = 60
TOWER_PANEL_HEIGHT = 100  # Hauteur de la zone des tours en bas
TOWER_SIZE = 40  # Taille des tours
VILLAGE_SIZE = 60  # Taille du village (plus grand que TOWER_SIZE qui est 40)
GO_BUTTON_WIDTH = 80
GO_BUTTON_HEIGHT = 40
SAVE_FILE = "map_save.json"
RANGE_ALPHA = 128  # Transparence des cercles de portée (0-255)
MONSTER_SIZE = 20  # Taille des triangles des monstres
WORLD_SIZE = 3000  # Taille du monde en pixels
MIN_SPAWN_DISTANCE = 800  # Distance minimale de spawn du village
MAX_SPAWN_DISTANCE = 1200  # Distance maximale de spawn du village
MAX_ZOOM = 4.0  # Au lieu de 2.0
MIN_ZOOM = 0.5  # Garder le minimum actuel
DEBUG_LINE_ALPHA = 128  # Transparence des lignes de debug
TIME_ACCELERATIONS = [1.0, 5.0, 10.0, 15.0, 20.0]  # Différents niveaux d'accélération
VILLAGE_MAX_HEALTH = 1000
VILLAGE_HEALTH_BAR_WIDTH = 200  # Largeur de la barre de vie du village
PROJECTILE_SPEED = 400  # Vitesse des projectiles en pixels par seconde
PROJECTILE_SIZE = 6    # Taille des projectiles
HEAL_RANGE = 150  # Portée de soin des sorcières
SPIRIT_BUFF_RANGE = 200  # Portée du buff des esprits
KAMIKAZE_EXPLOSION_RANGE = 100  # Portée de l'explosion des kamikazes
EXPLOSION_DURATION = 0.5  # Durée de l'explosion en secondes
EXPLOSION_MAX_RADIUS = 50  # Rayon maximum de l'explosion
LIGHT_MAX_RANGE = 500  # Distance maximale d'utilisation de la lumière depuis le village
LIGHT_MAX_POWER = 100  # Puissance maximale de la lumière
LIGHT_DRAIN_RATE = 15  # Vitesse de décharge (points par seconde)
LIGHT_RECHARGE_RATE = 10  # Vitesse de recharge (points par seconde)
LIGHT_POWER_BAR_WIDTH = 200  # Largeur de la barre de puissance
LIGHT_POWER_BAR_HEIGHT = 15  # Hauteur de la barre de puissance
LIGHT_RADIUS = 200    # Rayon d'effet de la lumière
MONSTER_FEAR_DURATION = 3.0  # Durée pendant laquelle le monstre fuit (en secondes)
MAX_FLEE_TIME = 15.0  # Temps maximum de fuite en secondes
FLEE_DISTANCE_MIN = 200  # Distance minimale de fuite
FLEE_DISTANCE_MAX = 400  # Distance maximale de fuite
FLEE_ANGLE_VARIATION = math.pi / 4  # Variation maximale de l'angle de fuite (±45 degrés)
MAX_VISIBILITY_RANGE = 800  # Distance maximale de visibilité depuis le village

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

class GameMode(Enum):
    EDIT = 1
    PLAY = 2

class TowerType(Enum):
    POWERFUL = 1    # Tour puissante
    MEDIUM = 2      # Tour moyenne
    WEAK = 3        # Tour faible

class MonsterType(Enum):
    SKELETON = auto()
    WOLF = auto()
    MORAY = auto()
    SMALL_SPIRIT = auto()
    FIRE_SKELETON = auto()
    WITCH = auto()
    KAMIKAZE = auto()
    GIANT_WOLF = auto()
    GIANT_SKELETON = auto()
    ROYAL_MORAY = auto()
    DRAGON = auto()

# Déplacer MONSTER_NAMES ici, après la définition de MonsterType
MONSTER_NAMES = {
    MonsterType.SKELETON: "Squelette",
    MonsterType.WOLF: "Loup",
    MonsterType.MORAY: "Murène",
    MonsterType.SMALL_SPIRIT: "Petit Esprit",
    MonsterType.FIRE_SKELETON: "Squelette de Feu",
    MonsterType.WITCH: "Sorcière",
    MonsterType.KAMIKAZE: "Kamikaze",
    MonsterType.GIANT_WOLF: "Loup Géant",
    MonsterType.GIANT_SKELETON: "Squelette Géant",
    MonsterType.ROYAL_MORAY: "Murène Royale",
    MonsterType.DRAGON: "Dragon"
}

class Projectile:
    def __init__(self, start_x, start_y, target, damage, color, speed=PROJECTILE_SPEED):
        self.x = start_x
        self.y = start_y
        self.target = target
        self.damage = damage
        self.color = color
        self.speed = speed  # Vitesse personnalisable
        self.reached = False
        
        # Calculer la direction vers la cible
        dx = target.x - start_x
        dy = target.y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        self.dx = (dx / distance) * self.speed
        self.dy = (dy / distance) * self.speed

    def update(self, delta_time):
        """Met à jour la position du projectile"""
        self.x += self.dx * delta_time
        self.y += self.dy * delta_time
        
        # Vérifier si le projectile a atteint sa cible
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        if dx*dx + dy*dy < (PROJECTILE_SIZE * 2)**2:
            self.reached = True
            return True
        return False

    def draw(self, screen, camera_x, camera_y, zoom):
        """Dessine le projectile"""
        screen_x = (self.x - camera_x) * zoom + WINDOW_WIDTH/2
        screen_y = (self.y - camera_y) * zoom + WINDOW_HEIGHT/2
        
        pygame.draw.circle(screen, self.color, 
                         (int(screen_x), int(screen_y)), 
                         int(PROJECTILE_SIZE * zoom))

class Tower:
    def __init__(self, tower_type, x, y):
        self.tower_type = tower_type
        self.x = x
        self.y = y
        
        # Définir les attributs selon le type de tour
        if tower_type == TowerType.POWERFUL:
            self.vision_range = 200
            self.attack_range = 180
            self.attack_speed = 2
            self.damage = 50
            self.max_health = 300  # Plus de vie car plus chère
        elif tower_type == TowerType.MEDIUM:
            self.vision_range = 150
            self.attack_range = 130
            self.attack_speed = 1.5
            self.damage = 30
            self.max_health = 200  # Vie moyenne
        else:  # WEAK
            self.vision_range = 100
            self.attack_range = 80
            self.attack_speed = 1
            self.damage = 15
            self.max_health = 100  # Vie faible
            
        self.current_health = self.max_health
        self.attack_cooldown = 0  # Temps restant avant la prochaine attaque
        self.target = None  # Monstre ciblé actuellement
        self.projectiles = []  # Liste des projectiles actifs
        self.max_targets = 3 if tower_type == TowerType.WEAK else 1
        self.is_dead = False  # Ajouter cet attribut

    def take_damage(self, amount):
        """Applique les dégâts à la tour"""
        self.current_health -= amount
        if self.current_health <= 0:
            self.is_dead = True
        return self.current_health <= 0

    def find_target(self, monsters):
        """Trouve une cible parmi les monstres à portée"""
        if self.target and self.target in monsters:  # Garder la cible actuelle si toujours valide
            dist = math.sqrt((self.target.x - self.x)**2 + (self.target.y - self.y)**2)
            if dist <= self.vision_range:
                return self.target
        
        # Chercher une nouvelle cible
        closest_dist = float('inf')
        closest_monster = None
        
        for monster in monsters:
            dist = math.sqrt((monster.x - self.x)**2 + (monster.y - self.y)**2)
            if dist <= self.vision_range and dist < closest_dist:
                closest_dist = dist
                closest_monster = monster
        
        self.target = closest_monster
        return closest_monster

    def find_targets(self, monsters):
        """Trouve plusieurs cibles pour la tour jaune"""
        if self.tower_type != TowerType.WEAK:
            target = self.find_target(monsters)
            return [target] if target else []

        targets = []
        for monster in monsters:
            dist = math.sqrt((monster.x - self.x)**2 + (monster.y - self.y)**2)
            if dist <= self.vision_range and len(targets) < self.max_targets:
                targets.append(monster)
        return targets

    def attack(self, monsters, delta_time):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= delta_time
            return

        for monster in monsters:
            dist = math.sqrt((monster.x - self.x)**2 + (monster.y - self.y)**2)
            if dist <= self.attack_range:
                color = BLUE if self.tower_type == TowerType.POWERFUL else \
                       GREEN if self.tower_type == TowerType.MEDIUM else YELLOW
                self.projectiles.append(
                    Projectile(self.x, self.y, monster, self.damage, color)
                )
        if monsters:
            self.attack_cooldown = 1 / self.attack_speed

    def update_projectiles(self, delta_time):
        """Met à jour tous les projectiles de la tour"""
        # Mettre à jour les projectiles et vérifier les impacts
        for projectile in self.projectiles[:]:  # Copie de la liste pour éviter les problèmes de suppression
            if projectile.update(delta_time):
                if not projectile.target.is_dead:  # Vérifier si la cible existe encore
                    projectile.target.take_damage(projectile.damage)
                self.projectiles.remove(projectile)
            elif projectile.target.is_dead:  # Si la cible est morte avant l'impact
                self.projectiles.remove(projectile)

class Monster:
    # Modifier MONSTER_STATS pour ajouter le pourcentage de groupage
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
        self.target_direction = initial_direction  # Direction vers laquelle on veut tourner
        self.rotation_speed = math.pi  # Vitesse de rotation en radians par seconde (180 degrés/s)
        
        # États supplémentaires
        self.is_fleeing = False
        self.flee_time = 0
        self.flee_target_x = None  # Position cible pour la fuite
        self.flee_target_y = None
        self.flee_distance = 300  # Distance de fuite
        self.target = None       # Cible actuelle (village ou tour)
        self.path = []          # Chemin vers la cible
        self.group_factor = stats['group_factor']
        self.current_target = None  # Ajouter cette ligne pour mémoriser la cible
        self.current_target_type = None  # 'tower' ou 'village'
        
        # Ajouter une probabilité de cibler le village directement
        self.target_village_chance = 0.15 if monster_type in [MonsterType.KAMIKAZE, 
                                                            MonsterType.DRAGON] else 0.05
        
        self.is_dead = False
        
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
        
        # Portée d'attaque pour les monstres à distance
        if self.can_shoot:
            self.effect_range = stats['attack_range']
            self.effect_color = (*self.color, 128)  # Couleur du monstre transparente

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
        if light_intensity * (self.light_fear / 100) > 0.5:  # Seuil arbitraire de 0.5
            self.is_fleeing = True
            return True
        self.is_fleeing = False
        return False

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

    def draw(self, screen, camera_x, camera_y, zoom, show_names=False, show_monster_ranges=False, village_x=None, village_y=None, towers=None):
        """Ne dessine le monstre que s'il est visible"""
        # Si le monstre n'est pas visible, ne pas le dessiner
        if not self.is_visible(village_x, village_y, towers):
            return
            
        # Calculer les trois points du triangle
        angle = math.pi / 4  # 45 degrés pour la largeur du triangle
        size = MONSTER_SIZE * zoom
        
        # Point avant du triangle (pointe)
        front_x = self.x + math.cos(self.direction) * size
        front_y = self.y + math.sin(self.direction) * size
        
        # Points arrière du triangle
        back_left_x = self.x + math.cos(self.direction + math.pi - angle) * size
        back_left_y = self.y + math.sin(self.direction + math.pi - angle) * size
        
        back_right_x = self.x + math.cos(self.direction + math.pi + angle) * size
        back_right_y = self.y + math.sin(self.direction + math.pi + angle) * size
        
        # Convertir en coordonnées écran
        points = [
            ((front_x - camera_x) * zoom + WINDOW_WIDTH/2, 
             (front_y - camera_y) * zoom + WINDOW_HEIGHT/2),
            ((back_left_x - camera_x) * zoom + WINDOW_WIDTH/2, 
             (back_left_y - camera_y) * zoom + WINDOW_HEIGHT/2),
            ((back_right_x - camera_x) * zoom + WINDOW_WIDTH/2, 
             (back_right_y - camera_y) * zoom + WINDOW_HEIGHT/2)
        ]
        
        # Dessiner le triangle
        pygame.draw.polygon(screen, self.color, points)
        
        # Barre de vie
        health_ratio = self.current_health / self.max_health
        health_width = MONSTER_SIZE * zoom
        health_height = 3 * zoom
        health_x = ((self.x - camera_x) * zoom + WINDOW_WIDTH/2) - health_width/2
        health_y = ((self.y - camera_y) * zoom + WINDOW_HEIGHT/2) - MONSTER_SIZE * zoom - health_height - 2
        
        # Fond de la barre de vie
        pygame.draw.rect(screen, (64, 64, 64),
                        (health_x, health_y, health_width, health_height))
        # Barre de vie actuelle
        pygame.draw.rect(screen, (0, 255, 0) if health_ratio > 0.5 else 
                                (255, 255, 0) if health_ratio > 0.25 else 
                                (255, 0, 0),
                        (health_x, health_y, health_width * health_ratio, health_height))
        
        # Barre de force d'attaque
        damage_ratio = self.current_damage / self.max_damage
        damage_y = health_y - health_height - 1
        # Fond de la barre de force
        pygame.draw.rect(screen, (64, 64, 64),
                        (health_x, damage_y, health_width, health_height))
        # Barre de force actuelle
        pygame.draw.rect(screen, (0, 0, 255),  # Bleu
                        (health_x, damage_y, health_width * damage_ratio, health_height))

        # Afficher le nom si activé
        if show_names:
            font = pygame.font.Font(None, int(20 * zoom))
            name_surface = font.render(MONSTER_NAMES[self.monster_type], True, self.color)
            name_x = ((self.x - camera_x) * zoom + WINDOW_WIDTH/2) - name_surface.get_width()/2
            name_y = ((self.y - camera_y) * zoom + WINDOW_HEIGHT/2) - MONSTER_SIZE * zoom - 20 * zoom
            screen.blit(name_surface, (name_x, name_y))

        # Afficher les zones d'effet si activé
        if show_monster_ranges and hasattr(self, 'effect_range'):
            range_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            screen_x, screen_y = (self.x - camera_x) * zoom + WINDOW_WIDTH/2, (self.y - camera_y) * zoom + WINDOW_HEIGHT/2
            
            # Dessiner le cercle d'effet
            radius = int(self.effect_range * zoom)
            pygame.draw.circle(range_surface, self.effect_color,
                             (int(screen_x), int(screen_y)), radius)
            
            screen.blit(range_surface, (0, 0))

        # Dessiner les projectiles du monstre
        for projectile in self.projectiles:
            projectile.draw(screen, camera_x, camera_y, zoom)

    def start_fleeing(self, light_position):
        """Démarre la fuite du monstre en calculant une position symétrique par rapport à sa position actuelle"""
        # Calculer la position cible symétrique par rapport à la position actuelle
        if self.current_target:
            # Obtenir la position de la cible actuelle
            target_x = self.current_target.x if self.current_target_type == 'tower' else self.village_x
            target_y = self.current_target.y if self.current_target_type == 'tower' else self.village_y
            
            # Calculer le point symétrique (à l'opposé de la cible actuelle)
            dx = self.x - target_x
            dy = self.y - target_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # La nouvelle cible est dans la même direction mais à la même distance
            self.flee_target_x = self.x + dx
            self.flee_target_y = self.y + dy
            
            # Limiter la position cible dans les limites du monde
            self.flee_target_x = max(0, min(self.flee_target_x, WORLD_SIZE))
            self.flee_target_y = max(0, min(self.flee_target_y, WORLD_SIZE))
            
            # Calculer le temps de fuite basé sur le pourcentage de peur
            fear_factor = self.MONSTER_STATS[self.monster_type]['light_fear'] / 100.0
            self.flee_time = MAX_FLEE_TIME * fear_factor
            
            # Réinitialiser la cible actuelle
            self.is_fleeing = True
            self.current_target = None
            self.current_target_type = None

    def update(self, towers, village_x, village_y, delta_time, light_position=None, light_active=False, light_power=0):
        if self.is_fleeing:
            # Mise à jour du temps de fuite
            self.flee_time -= delta_time
            if self.flee_time <= 0:
                self.is_fleeing = False
                self.flee_target_x = None
                self.flee_target_y = None
                self.current_target = None
                self.current_target_type = None
            else:
                # Se déplacer vers la position cible de fuite
                dx = self.flee_target_x - self.x
                dy = self.flee_target_y - self.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > 5:
                    # Calculer la direction cible
                    self.target_direction = math.atan2(dy, dx)
                    
                    # Rotation progressive
                    angle_diff = (self.target_direction - self.direction + math.pi) % (2 * math.pi) - math.pi
                    max_rotation = self.rotation_speed * delta_time
                    if abs(angle_diff) > max_rotation:
                        if angle_diff > 0:
                            self.direction += max_rotation
                        else:
                            self.direction -= max_rotation
                    else:
                        self.direction = self.target_direction
                    
                    # Normaliser et appliquer la vitesse (x2 pendant la fuite)
                    flee_speed = self.speed * 2
                    self.x += (dx / distance) * flee_speed * delta_time
                    self.y += (dy / distance) * flee_speed * delta_time
                return

        # Si la lumière est active et qu'il reste de la puissance, vérifier si le monstre doit fuir
        if light_active and light_position and light_power > 0:
            dist_to_light = math.sqrt((light_position[0] - self.x)**2 + 
                                    (light_position[1] - self.y)**2)
            if dist_to_light < LIGHT_RADIUS:
                # Calculer la probabilité de fuite basée sur la sensibilité à la lumière
                if random.random() * 100 < self.MONSTER_STATS[self.monster_type]['light_fear']:
                    self.start_fleeing(light_position)
                    return

        # Comportement normal si pas en fuite
        if not self.is_fleeing:
            # Si pas de cible actuelle ou si la cible (tour) a été détruite
            if (self.current_target is None or 
                (self.current_target_type == 'tower' and self.current_target not in towers)):
                
                # Choisir une nouvelle cible
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

            # Déplacement vers la cible
            target_x = self.current_target.x if self.current_target_type == 'tower' else village_x
            target_y = self.current_target.y if self.current_target_type == 'tower' else village_y
            
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 5:
                # Calculer la direction cible
                self.target_direction = math.atan2(dy, dx)
                
                # Rotation progressive
                angle_diff = (self.target_direction - self.direction + math.pi) % (2 * math.pi) - math.pi
                max_rotation = self.rotation_speed * delta_time
                if abs(angle_diff) > max_rotation:
                    if angle_diff > 0:
                        self.direction += max_rotation
                    else:
                        self.direction -= max_rotation
                else:
                    self.direction = self.target_direction
                
                # Déplacer le monstre dans la direction actuelle
                speed = self.speed * delta_time
                self.x += math.cos(self.direction) * speed
                self.y += math.sin(self.direction) * speed

            # Gestion des projectiles existants
            for projectile in self.projectiles[:]:
                if projectile.update(delta_time):
                    if projectile.target in towers:  # Si la cible est une tour
                        if projectile.target.take_damage(self.current_damage):
                            # Si la tour est détruite
                            towers.remove(projectile.target)
                            if self.current_target == projectile.target:
                                self.current_target = None
                                self.current_target_type = None
                    self.projectiles.remove(projectile)
                elif projectile.target not in towers:  # Si la tour n'existe plus
                    self.projectiles.remove(projectile)

            # Attaque à distance pour les murènes et dragons
            if self.can_shoot and self.current_target_type == 'tower':
                if self.attack_cooldown > 0:
                    self.attack_cooldown -= delta_time
                else:
                    dist = math.sqrt((self.current_target.x - self.x)**2 + 
                               (self.current_target.y - self.y)**2)
                    # Attaquer si dans la zone d'attaque mais pas trop proche
                    if self.attack_range >= dist >= TOWER_SIZE * 2:
                        self.projectiles.append(
                            Projectile(self.x, self.y, self.current_target, 
                                     self.current_damage, self.color, self.projectile_speed)
                        )
                        self.attack_cooldown = 1 / self.attack_speed

    def die(self, game):
        """Appelé quand le monstre meurt"""
        if self.monster_type == MonsterType.KAMIKAZE:
            # Créer une explosion et infliger des dégâts aux tours proches
            game.create_explosion(self.x, self.y, KAMIKAZE_EXPLOSION_RANGE, self.color)
            for tower in game.towers:
                dist = math.sqrt((tower.x - self.x)**2 + (tower.y - self.y)**2)
                if dist <= KAMIKAZE_EXPLOSION_RANGE:
                    damage_factor = 1 - (dist / KAMIKAZE_EXPLOSION_RANGE)  # Plus de dégâts au centre
                    tower.take_damage(self.current_damage * damage_factor)

@dataclass
class WaveMonster:
    monster_type: MonsterType
    count: int
    spawn_delay: float  # Délai entre chaque monstre en secondes

@dataclass
class Wave:
    monsters: List[WaveMonster]
    spawn_distance: float  # Distance de spawn du village
    wave_delay: float     # Délai avant la prochaine vague en secondes

class WaveManager:
    def __init__(self, village_x, village_y):
        self.village_x = village_x
        self.village_y = village_y
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
                
            return Monster(monster_type, x, y, initial_direction=angle)
            
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

class Explosion:
    def __init__(self, x, y, max_radius, duration, color):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.duration = duration
        self.color = color
        self.time = 0
        self.finished = False
    
    def update(self, delta_time):
        self.time += delta_time
        if self.time >= self.duration:
            self.finished = True
    
    def draw(self, screen, camera_x, camera_y, zoom):
        if not self.finished:
            progress = self.time / self.duration
            current_radius = self.max_radius * progress
            alpha = int(255 * (1 - progress))
            
            screen_x = (self.x - camera_x) * zoom + WINDOW_WIDTH/2
            screen_y = (self.y - camera_y) * zoom + WINDOW_HEIGHT/2
            
            explosion_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(explosion_surface, 
                             (*self.color, alpha),
                             (int(screen_x), int(screen_y)), 
                             int(current_radius * zoom))
            screen.blit(explosion_surface, (0, 0))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Tower Defense")
        self.clock = pygame.time.Clock()
        
        self.game_mode = GameMode.EDIT
        self.towers = []
        
        # Position du village (centre de la carte)
        self.village_x = WORLD_SIZE // 2
        self.village_y = WORLD_SIZE // 2
        
        # Initialiser la caméra centrée sur le village
        self.camera_x = self.village_x
        self.camera_y = self.village_y
        self.zoom = 1.0
        
        # Point central de l'écran pour le zoom
        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT // 2
        
        # Tours disponibles
        self.available_towers = [
            {'type': TowerType.POWERFUL, 'count': 1, 'color': BLUE},    # 1 tour puissante
            {'type': TowerType.MEDIUM, 'count': 2, 'color': GREEN},     # 2 tours moyennes
            {'type': TowerType.WEAK, 'count': 3, 'color': YELLOW}       # 3 tours faibles
        ]
        
        # Variables pour le drag & drop
        self.dragged_tower = None
        self.selected_tower = None
        self.dragging_map = False
        self.last_mouse_pos = None
        self.mouse_x = 0
        self.mouse_y = 0
        
        # Bouton GO
        self.go_button_rect = pygame.Rect(
            WINDOW_WIDTH - GO_BUTTON_WIDTH - 10,
            WINDOW_HEIGHT - TOWER_PANEL_HEIGHT + (TOWER_PANEL_HEIGHT - GO_BUTTON_HEIGHT) // 2,
            GO_BUTTON_WIDTH,
            GO_BUTTON_HEIGHT
        )
        
        self.show_ranges = False
        self.wave_manager = None
        self.game_start_time = 0
        self.monsters = []
        self.show_debug = False
        self.time_acceleration_index = 0
        self.time_accelerated = False
        self.village_health = VILLAGE_MAX_HEALTH
        self.game_over = False
        self.show_names = False
        self.show_monster_ranges = False
        self.explosions = []  # Liste des explosions en cours
        self.light_power = LIGHT_MAX_POWER
        self.light_active = False
        self.light_position = None
        
        # Charger la sauvegarde si elle existe
        self.load_map()

    def world_to_screen(self, x, y):
        """Convertit les coordonnées du monde en coordonnées écran"""
        screen_x = (x - self.camera_x) * self.zoom + self.center_x
        screen_y = (y - self.camera_y) * self.zoom + self.center_y
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        """Convertit les coordonnées écran en coordonnées du monde"""
        world_x = (screen_x - self.center_x) / self.zoom + self.camera_x
        world_y = (screen_y - self.center_y) / self.zoom + self.camera_y
        return world_x, world_y

    def get_tower_at_position(self, x, y):
        """Retourne la tour à la position donnée"""
        for tower in self.towers:
            screen_x, screen_y = self.world_to_screen(tower.x, tower.y)
            if (x - screen_x) ** 2 + (y - screen_y) ** 2 < (TOWER_SIZE/2) ** 2:
                return tower
        return None
    
    def is_position_valid(self, x, y, ignore_tower=None):
        """Vérifie si une position est valide pour placer une tour"""
        # Vérifier la collision avec le village
        village_screen_x, village_screen_y = self.world_to_screen(self.village_x, self.village_y)
        if (x - village_screen_x) ** 2 + (y - village_screen_y) ** 2 < (VILLAGE_SIZE) ** 2:
            return False
            
        # Vérifier la collision avec les autres tours
        for tower in self.towers:
            if tower == ignore_tower:
                continue
            screen_x, screen_y = self.world_to_screen(tower.x, tower.y)
            if (x - screen_x) ** 2 + (y - screen_y) ** 2 < (TOWER_SIZE) ** 2:
                return False
        return True

    def all_towers_placed(self):
        """Vérifie si toutes les tours ont été placées"""
        return all(tower_info['count'] == 0 for tower_info in self.available_towers)

    def start_game(self):
        """Démarre le mode jeu"""
        self.game_mode = GameMode.PLAY
        self.wave_manager = WaveManager(self.village_x, self.village_y)
        self.game_start_time = time.time()
        self.monsters = []
        
        # Recentrer la caméra sur le village
        self.camera_x = self.village_x
        self.camera_y = self.village_y
        self.zoom = 0.8  # Dézoomer un peu pour voir plus de terrain

    def handle_input(self):
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Gestion du zoom (disponible dans tous les modes)
                if event.button == 4:  # Molette vers le haut (zoom)
                    world_x, world_y = self.screen_to_world(self.mouse_x, self.mouse_y)
                    self.zoom = min(MAX_ZOOM, self.zoom * 1.1)  # Utiliser MAX_ZOOM
                    new_world_x, new_world_y = self.screen_to_world(self.mouse_x, self.mouse_y)
                    self.camera_x += (new_world_x - world_x)
                    self.camera_y += (new_world_y - world_y)
                    
                elif event.button == 5:  # Molette vers le bas (dézoom)
                    world_x, world_y = self.screen_to_world(self.mouse_x, self.mouse_y)
                    self.zoom = max(MIN_ZOOM, self.zoom / 1.1)
                    new_world_x, new_world_y = self.screen_to_world(self.mouse_x, self.mouse_y)
                    self.camera_x += (new_world_x - world_x)
                    self.camera_y += (new_world_y - world_y)
                    
                # Gestion du déplacement de la carte (disponible dans tous les modes)
                elif event.button == 2:  # Clic milieu
                    self.dragging_map = True
                    self.last_mouse_pos = (self.mouse_x, self.mouse_y)
                
                # Gestion des clics gauche et droit
                elif event.button == 1:  # Clic gauche
                    # Vérifier si on clique sur le bouton GO
                    if self.game_mode == GameMode.EDIT and self.go_button_rect.collidepoint(self.mouse_x, self.mouse_y):
                        if self.all_towers_placed():
                            self.save_map()
                            self.start_game()
                        return True
                    
                    # Gestion des tours (uniquement en mode EDIT)
                    if self.game_mode == GameMode.EDIT:
                        if self.mouse_y > WINDOW_HEIGHT - TOWER_PANEL_HEIGHT:
                            if not self.go_button_rect.collidepoint(self.mouse_x, self.mouse_y):
                                panel_x = 10
                                for tower_info in self.available_towers:
                                    if tower_info['count'] > 0:
                                        tower_rect = pygame.Rect(panel_x, WINDOW_HEIGHT - TOWER_PANEL_HEIGHT + 10, 
                                                              TOWER_SIZE, TOWER_SIZE)
                                        if tower_rect.collidepoint(self.mouse_x, self.mouse_y):
                                            self.dragged_tower = {'type': tower_info['type'], 'info': tower_info}
                                    panel_x += TOWER_SIZE + 10
                        else:
                            clicked_tower = self.get_tower_at_position(self.mouse_x, self.mouse_y)
                            if clicked_tower:
                                self.selected_tower = clicked_tower
                                self.dragged_tower = {'type': clicked_tower.tower_type, 
                                                    'existing': clicked_tower}
                            elif not self.dragged_tower:
                                self.dragging_map = True
                                self.last_mouse_pos = (self.mouse_x, self.mouse_y)
                    else:  # En mode PLAY
                        # Démarrer le déplacement de la carte si on clique sur une zone vide
                        self.dragging_map = True
                        self.last_mouse_pos = (self.mouse_x, self.mouse_y)
                    
                elif event.button == 3 and self.game_mode == GameMode.EDIT and self.selected_tower:  # Clic droit
                    if self.selected_tower in self.towers:
                        self.towers.remove(self.selected_tower)
                        for tower_info in self.available_towers:
                            if tower_info['type'] == self.selected_tower.tower_type:
                                tower_info['count'] += 1
                        self.selected_tower = None
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Relâchement clic gauche
                    if self.game_mode == GameMode.EDIT and self.dragged_tower:  # Fin du drag & drop d'une tour
                        world_x, world_y = self.screen_to_world(self.mouse_x, self.mouse_y)
                        
                        if self.mouse_y < WINDOW_HEIGHT - TOWER_PANEL_HEIGHT and \
                           self.is_position_valid(self.mouse_x, self.mouse_y, self.dragged_tower.get('existing')):
                            
                            if 'existing' in self.dragged_tower:
                                self.dragged_tower['existing'].x = world_x
                                self.dragged_tower['existing'].y = world_y
                            else:
                                self.towers.append(Tower(self.dragged_tower['type'], world_x, world_y))
                                self.dragged_tower['info']['count'] -= 1
                        
                        self.dragged_tower = None
                    self.dragging_map = False
                
                elif event.button == 2:  # Relâchement clic milieu
                    self.dragging_map = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Touche R pour afficher/masquer les ranges
                    self.show_ranges = not self.show_ranges
                elif event.key == pygame.K_d:  # Touche D pour afficher/masquer le debug
                    self.show_debug = not self.show_debug
                elif event.key == pygame.K_n:  # Touche N pour afficher/masquer les noms
                    self.show_names = not self.show_names
                elif event.key == pygame.K_m:  # Touche M pour afficher/masquer les zones d'effet des monstres
                    self.show_monster_ranges = not self.show_monster_ranges
                elif event.key == pygame.K_t:  # Touche T pour changer l'accélération du temps
                    self.time_acceleration_index = (self.time_acceleration_index + 1) % len(TIME_ACCELERATIONS)
                    self.time_accelerated = self.time_acceleration_index > 0
        
        # Déplacement de la carte par drag (disponible dans tous les modes)
        if self.dragging_map and self.last_mouse_pos:
            dx = self.mouse_x - self.last_mouse_pos[0]
            dy = self.mouse_y - self.last_mouse_pos[1]
            self.camera_x -= dx / self.zoom
            self.camera_y -= dy / self.zoom
            self.last_mouse_pos = (self.mouse_x, self.mouse_y)
            
        # Gestion de la lumière avec le clic droit
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[2]:  # Clic droit
            mouse_world_pos = self.screen_to_world(self.mouse_x, self.mouse_y)
            dist_to_village = math.sqrt((mouse_world_pos[0] - self.village_x)**2 + 
                                      (mouse_world_pos[1] - self.village_y)**2)
            
            # Vérifier aussi la distance aux tours
            is_in_valid_zone = dist_to_village <= LIGHT_MAX_RANGE
            for tower in self.towers:
                dist_to_tower = math.sqrt((mouse_world_pos[0] - tower.x)**2 + 
                                        (mouse_world_pos[1] - tower.y)**2)
                if dist_to_tower <= tower.vision_range:
                    is_in_valid_zone = True
                    break
            
            if is_in_valid_zone and self.light_power > 0:
                self.light_active = True
                self.light_position = mouse_world_pos
            else:
                self.light_active = False
                self.light_position = None
        else:
            self.light_active = False
            self.light_position = None
        
        return True

    def update(self):
        """Mise à jour de la logique du jeu"""
        if self.game_mode == GameMode.PLAY and not self.game_over:
            current_time = time.time() - self.game_start_time
            
            # Calculer le delta_time en fonction de l'accélération
            base_delta = 1 / FPS
            delta_time = base_delta * TIME_ACCELERATIONS[self.time_acceleration_index]
            
            # Spawn des nouveaux monstres
            new_monster = self.wave_manager.update(current_time)
            if new_monster:
                self.monsters.append(new_monster)
            
            # Mise à jour des tours et de leurs projectiles
            for tower in self.towers:
                targets = tower.find_targets(self.monsters)
                tower.attack(targets, delta_time)
                tower.update_projectiles(delta_time)
            
            # Mise à jour des monstres et nettoyage des morts
            self.monsters = [monster for monster in self.monsters if not monster.is_dead]
            
            for monster in self.monsters:
                monster.update(self.towers, self.village_x, self.village_y, delta_time,
                             self.light_position, self.light_active, self.light_power)
                
                # Vérifier les attaques
                if monster.current_target_type == 'tower' and monster.current_target:
                    dist = math.sqrt((monster.current_target.x - monster.x)**2 + 
                                   (monster.current_target.y - monster.y)**2)
                    
                    if dist < TOWER_SIZE:  # Si le monstre est assez proche de la tour
                        if monster.current_target.take_damage(
                            monster.current_damage * delta_time * monster.attack_speed):
                            # Si la tour est détruite
                            self.towers.remove(monster.current_target)
                            monster.current_target = None
                            monster.current_target_type = None
                
                elif monster.current_target_type == 'village':
                    dist = math.sqrt((self.village_x - monster.x)**2 + 
                                   (self.village_y - monster.y)**2)
                    
                    if dist < VILLAGE_SIZE:  # Si le monstre est assez proche du village
                        # Infliger des dégâts au village
                        self.village_health -= monster.current_damage * delta_time * monster.attack_speed
                        if self.village_health <= 0:
                            self.game_over = True

            # Mise à jour des explosions
            self.explosions = [exp for exp in self.explosions if not exp.finished]
            for explosion in self.explosions:
                explosion.update(delta_time)

            # Mise à jour de la puissance de la lumière
            if self.light_active:
                self.light_power = max(0, self.light_power - LIGHT_DRAIN_RATE * delta_time)
            else:
                self.light_power = min(LIGHT_MAX_POWER, self.light_power + LIGHT_RECHARGE_RATE * delta_time)

    def draw(self):
        self.screen.fill(BLACK)
        
        # Dessiner la grille
        # Calculer les limites de la grille visible
        grid_start_x = int(self.camera_x - WINDOW_WIDTH / (2 * self.zoom))
        grid_end_x = int(self.camera_x + WINDOW_WIDTH / (2 * self.zoom))
        grid_start_y = int(self.camera_y - WINDOW_HEIGHT / (2 * self.zoom))
        grid_end_y = int(self.camera_y + WINDOW_HEIGHT / (2 * self.zoom))
        
        # Arrondir aux multiples de GRID_SIZE
        grid_start_x = (grid_start_x // GRID_SIZE) * GRID_SIZE
        grid_end_x = (grid_end_x // GRID_SIZE + 1) * GRID_SIZE
        grid_start_y = (grid_start_y // GRID_SIZE) * GRID_SIZE
        grid_end_y = (grid_end_y // GRID_SIZE + 1) * GRID_SIZE
        
        # Dessiner les lignes verticales
        for x in range(grid_start_x, grid_end_x + GRID_SIZE, GRID_SIZE):
            start_pos = self.world_to_screen(x, grid_start_y)
            end_pos = self.world_to_screen(x, grid_end_y)
            pygame.draw.line(self.screen, GRAY, 
                            (int(start_pos[0]), int(start_pos[1])), 
                            (int(end_pos[0]), int(end_pos[1])))
        # Dessiner les lignes horizontales
        for y in range(grid_start_y, grid_end_y + GRID_SIZE, GRID_SIZE):
            start_pos = self.world_to_screen(grid_start_x, y)
            end_pos = self.world_to_screen(grid_end_x, y)
            pygame.draw.line(self.screen, GRAY, 
                            (int(start_pos[0]), int(start_pos[1])), 
                            (int(end_pos[0]), int(end_pos[1])))
        
        # Dessiner le village
        village_screen_x, village_screen_y = self.world_to_screen(self.village_x, self.village_y)
        village_radius = int(VILLAGE_SIZE/2 * self.zoom)
        pygame.draw.circle(self.screen, RED, (int(village_screen_x), int(village_screen_y)), village_radius)
        
        # Dessiner les tours placées
        for tower in self.towers:
            screen_x, screen_y = self.world_to_screen(tower.x, tower.y)
            
            # Déterminer la couleur de la tour
            color = BLUE if tower.tower_type == TowerType.POWERFUL else \
                   GREEN if tower.tower_type == TowerType.MEDIUM else YELLOW
            
            # Dessiner les zones d'attaque si activé
            if self.show_ranges:
                # Créer une surface transparente pour le range
                range_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                
                # Dessiner le cercle de vision
                vision_radius = int(tower.vision_range * self.zoom)
                pygame.draw.circle(range_surface, (*color, RANGE_ALPHA//2),
                                 (int(screen_x), int(screen_y)), vision_radius)
                
                # Dessiner le cercle d'attaque
                attack_radius = int(tower.attack_range * self.zoom)
                pygame.draw.circle(range_surface, (*color, RANGE_ALPHA),
                                 (int(screen_x), int(screen_y)), attack_radius)
                
                # Appliquer la surface transparente sur l'écran
                self.screen.blit(range_surface, (0, 0))
            
            # Dessiner la tour avec une barre de vie
            pygame.draw.circle(self.screen, color, 
                             (int(screen_x), int(screen_y)), 
                             int(TOWER_SIZE/2 * self.zoom))
            
            # Dessiner la barre de vie
            health_ratio = tower.current_health / tower.max_health
            health_width = TOWER_SIZE * self.zoom
            health_height = 5 * self.zoom
            health_x = screen_x - health_width/2
            health_y = screen_y + (TOWER_SIZE/2 + 5) * self.zoom
            
            # Fond de la barre de vie
            pygame.draw.rect(self.screen, (64, 64, 64),
                            (health_x, health_y, health_width, health_height))
            # Barre de vie actuelle
            pygame.draw.rect(self.screen, (0, 255, 0) if health_ratio > 0.5 else 
                                         (255, 255, 0) if health_ratio > 0.25 else 
                                         (255, 0, 0),
                            (health_x, health_y, health_width * health_ratio, health_height))
            
            # Afficher la sélection
            if tower == self.selected_tower:
                pygame.draw.circle(self.screen, WHITE, 
                                 (int(screen_x), int(screen_y)), 
                                 int(TOWER_SIZE/2 * self.zoom), 2)
        
        # Dessiner le panel des tours disponibles
        if self.game_mode == GameMode.EDIT:
            pygame.draw.rect(self.screen, GRAY, 
                           (0, WINDOW_HEIGHT - TOWER_PANEL_HEIGHT, 
                            WINDOW_WIDTH, TOWER_PANEL_HEIGHT))
            
            panel_x = 10
            for tower_info in self.available_towers:
                if tower_info['count'] > 0:
                    pygame.draw.circle(self.screen, tower_info['color'],
                                     (panel_x + TOWER_SIZE//2, 
                                      WINDOW_HEIGHT - TOWER_PANEL_HEIGHT + TOWER_SIZE//2),
                                     TOWER_SIZE//2)
                    # Afficher le nombre restant
                    count_text = str(tower_info['count'])
                    text_surface = pygame.font.Font(None, 24).render(count_text, True, WHITE)
                    self.screen.blit(text_surface, 
                                   (panel_x + TOWER_SIZE//2 - 5, 
                                    WINDOW_HEIGHT - TOWER_PANEL_HEIGHT + TOWER_SIZE + 5))
                panel_x += TOWER_SIZE + 10
            
            # Dessiner le bouton GO
            button_color = GREEN if self.all_towers_placed() else GRAY  # Gris si toutes les tours ne sont pas placées
            if self.game_mode == GameMode.PLAY:
                button_color = RED
            pygame.draw.rect(self.screen, button_color, self.go_button_rect)
            
            # Texte du bouton
            button_text = "GO!" if self.game_mode == GameMode.EDIT else "EDIT"
            font = pygame.font.Font(None, 36)
            text_color = WHITE if self.all_towers_placed() or self.game_mode == GameMode.PLAY else (128, 128, 128)  # Gris clair si inactif
            text_surface = font.render(button_text, True, text_color)
            text_rect = text_surface.get_rect(center=self.go_button_rect.center)
            self.screen.blit(text_surface, text_rect)
        
        # Dessiner la tour en cours de drag & drop
        if self.dragged_tower:
            color = BLUE if self.dragged_tower['type'] == TowerType.POWERFUL else \
                   GREEN if self.dragged_tower['type'] == TowerType.MEDIUM else YELLOW
            pygame.draw.circle(self.screen, color, 
                             (self.mouse_x, self.mouse_y), TOWER_SIZE//2)
            
            # Montrer si la position est valide
            if self.mouse_y < WINDOW_HEIGHT - TOWER_PANEL_HEIGHT:
                valid = self.is_position_valid(self.mouse_x, self.mouse_y, 
                                            self.dragged_tower.get('existing'))
                pygame.draw.circle(self.screen, WHITE if valid else RED,
                                 (self.mouse_x, self.mouse_y), TOWER_SIZE//2, 2)
        
        # Afficher le mode de jeu actuel (fixe à l'écran, pas affecté par le zoom)
        font = pygame.font.Font(None, 36)
        mode_text = "Mode: " + self.game_mode.name
        text_surface = font.render(mode_text, True, WHITE)
        self.screen.blit(text_surface, (10, 10))
        
        # Dessiner les monstres (après la grille mais avant l'interface)
        for monster in self.monsters:
            # Ne dessiner le monstre et ses lignes de debug que s'il est visible
            if monster.is_visible(self.village_x, self.village_y, self.towers):
                monster.draw(self.screen, self.camera_x, self.camera_y, self.zoom, 
                           self.show_names, self.show_monster_ranges,
                           self.village_x, self.village_y, self.towers)  # Ajouter les paramètres manquants
                
                # Dessiner les lignes de debug si activé
                if self.show_debug:
                    debug_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                    monster_screen_x, monster_screen_y = self.world_to_screen(monster.x, monster.y)
                    
                    # Position de la cible à l'écran
                    if monster.is_fleeing and monster.flee_target_x is not None:
                        target_screen_x, target_screen_y = self.world_to_screen(
                            monster.flee_target_x,
                            monster.flee_target_y
                        )
                    elif monster.current_target_type == 'tower' and monster.current_target:
                        target_screen_x, target_screen_y = self.world_to_screen(
                            monster.current_target.x, 
                            monster.current_target.y
                        )
                    else:
                        target_screen_x, target_screen_y = self.world_to_screen(
                            self.village_x, 
                            self.village_y
                        )
                    
                    # Dessiner la ligne de direction
                    pygame.draw.line(
                        debug_surface,
                        (*monster.color, DEBUG_LINE_ALPHA),
                        (monster_screen_x, monster_screen_y),
                        (target_screen_x, target_screen_y),
                        max(1, int(2 * self.zoom))
                    )
                    
                    # Dessiner un petit cercle autour de la cible actuelle
                    circle_color = (255, 255, 0, DEBUG_LINE_ALPHA) if monster.is_fleeing else (*monster.color, DEBUG_LINE_ALPHA)
                    pygame.draw.circle(
                        debug_surface,
                        circle_color,
                        (int(target_screen_x), int(target_screen_y)),
                        int(10 * self.zoom),
                        2
                    )
                    
                    # Appliquer la surface de debug
                    self.screen.blit(debug_surface, (0, 0))
        
        # Afficher l'indicateur d'accélération du temps
        if self.time_accelerated:
            speed_text = f"x{TIME_ACCELERATIONS[self.time_acceleration_index]}"
            text_surface = font.render(speed_text, True, (255, 255, 0))
            self.screen.blit(text_surface, (WINDOW_WIDTH - 60, 10))
        
        # Dessiner le village avec sa barre de vie
        village_screen_x, village_screen_y = self.world_to_screen(self.village_x, self.village_y)
        village_radius = int(VILLAGE_SIZE/2 * self.zoom)
        pygame.draw.circle(self.screen, RED, (int(village_screen_x), int(village_screen_y)), village_radius)
        
        # Barre de vie du village
        health_ratio = max(0, self.village_health / VILLAGE_MAX_HEALTH)
        health_width = VILLAGE_HEALTH_BAR_WIDTH * self.zoom
        health_height = 10 * self.zoom
        health_x = village_screen_x - health_width/2
        health_y = village_screen_y - village_radius - health_height - 5
        
        # Fond de la barre de vie
        pygame.draw.rect(self.screen, (64, 64, 64),
                        (health_x, health_y, health_width, health_height))
        # Barre de vie actuelle
        pygame.draw.rect(self.screen, (0, 255, 0) if health_ratio > 0.5 else 
                                     (255, 255, 0) if health_ratio > 0.25 else 
                                     (255, 0, 0),
                        (health_x, health_y, health_width * health_ratio, health_height))
        
        # Dessiner les projectiles des tours
        for tower in self.towers:
            for projectile in tower.projectiles:
                projectile.draw(self.screen, self.camera_x, self.camera_y, self.zoom)
        
        # Dessiner les explosions
        for explosion in self.explosions:
            explosion.draw(self.screen, self.camera_x, self.camera_y, self.zoom)
        
        # Créer une seule surface pour toutes les zones de lumière
        if self.game_mode == GameMode.PLAY:
            light_zones_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            
            # Zone autour du village
            village_screen_x, village_screen_y = self.world_to_screen(self.village_x, self.village_y)
            pygame.draw.circle(light_zones_surface, (255, 255, 255, 30),
                             (int(village_screen_x), int(village_screen_y)),
                             int(LIGHT_MAX_RANGE * self.zoom))
            
            # Zones autour des tours
            for tower in self.towers:
                screen_x, screen_y = self.world_to_screen(tower.x, tower.y)
                pygame.draw.circle(light_zones_surface, (255, 255, 255, 30),
                                 (int(screen_x), int(screen_y)),
                                 int(tower.vision_range * self.zoom))
            
            # Appliquer toutes les zones de lumière en une seule fois
            self.screen.blit(light_zones_surface, (0, 0))
            
            # Dessiner l'indicateur de lumière autour du curseur
            mouse_world_pos = self.screen_to_world(self.mouse_x, self.mouse_y)
            
            # Vérifier si le curseur est dans une zone valide
            is_in_valid_zone = False
            
            # Vérifier la distance par rapport au village
            dist_to_village = math.sqrt((mouse_world_pos[0] - self.village_x)**2 + 
                                      (mouse_world_pos[1] - self.village_y)**2)
            if dist_to_village <= LIGHT_MAX_RANGE:
                is_in_valid_zone = True
            
            # Vérifier la distance par rapport aux tours
            for tower in self.towers:
                dist_to_tower = math.sqrt((mouse_world_pos[0] - tower.x)**2 + 
                                        (mouse_world_pos[1] - tower.y)**2)
                if dist_to_tower <= tower.vision_range:
                    is_in_valid_zone = True
                    break
            
            # Afficher l'indicateur de lumière si dans une zone valide et qu'il reste de la puissance
            if is_in_valid_zone and self.light_power > 0:
                cursor_light = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(cursor_light, (255, 255, 200, 50),
                                 (self.mouse_x, self.mouse_y),
                                 int(LIGHT_RADIUS * self.zoom))
                pygame.draw.circle(cursor_light, (255, 255, 200, 150),
                                 (self.mouse_x, self.mouse_y),
                                 int(LIGHT_RADIUS * self.zoom), 2)
                self.screen.blit(cursor_light, (0, 0))
                
                # Texte d'aide
                font = pygame.font.Font(None, 20)
                help_text = "Clic droit pour activer la lumière"
                text_surface = font.render(help_text, True, (255, 255, 200))
                self.screen.blit(text_surface, (self.mouse_x + 20, self.mouse_y + 20))
            
            # Dessiner la barre de puissance de la lumière près du curseur (plus petite)
            power_ratio = self.light_power / LIGHT_MAX_POWER
            bar_width = 50  # Barre plus petite
            bar_height = 5  # Barre plus fine
            bar_x = self.mouse_x - bar_width/2
            bar_y = self.mouse_y - 20  # Au-dessus du curseur
            
            # Fond de la barre
            pygame.draw.rect(self.screen, (64, 64, 64),
                            (bar_x, bar_y, bar_width, bar_height))
            # Barre de puissance
            pygame.draw.rect(self.screen, (255, 255, 200),
                            (bar_x, bar_y, bar_width * power_ratio, bar_height))
            
            # Dessiner la lumière active
            if self.light_active and self.light_position:
                light_screen_pos = self.world_to_screen(self.light_position[0], self.light_position[1])
                light_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(light_surface, (255, 255, 200, 100),
                                 (int(light_screen_pos[0]), int(light_screen_pos[1])),
                                  int(LIGHT_RADIUS * self.zoom))
                self.screen.blit(light_surface, (0, 0))
        
        # Afficher Game Over si nécessaire
        if self.game_over:
            font_big = pygame.font.Font(None, 74)
            game_over_text = font_big.render("GAME OVER", True, (255, 0, 0))
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
            self.screen.blit(game_over_text, text_rect)
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

    def save_map(self):
        """Sauvegarde la position des tours dans un fichier"""
        save_data = {
            'towers': [
                {
                    'type': tower.tower_type.value,
                    'x': tower.x,
                    'y': tower.y
                }
                for tower in self.towers
            ]
        }
        
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(save_data, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")

    def load_map(self):
        """Charge la position des tours depuis le fichier de sauvegarde"""
        if not os.path.exists(SAVE_FILE):
            return
        
        try:
            with open(SAVE_FILE, 'r') as f:
                save_data = json.load(f)
                
            # Réinitialiser les tours
            self.towers = []
            
            # Recréer les tours depuis la sauvegarde
            for tower_data in save_data['towers']:
                tower_type = TowerType(tower_data['type'])
                self.towers.append(Tower(tower_type, tower_data['x'], tower_data['y']))
                
                # Mettre à jour le compteur de tours disponibles
                for tower_info in self.available_towers:
                    if tower_info['type'] == tower_type:
                        tower_info['count'] -= 1
                        
        except Exception as e:
            print(f"Erreur lors du chargement: {e}")

    def create_explosion(self, x, y, max_radius, color):
        self.explosions.append(Explosion(x, y, max_radius, EXPLOSION_DURATION, color))

if __name__ == "__main__":
    game = Game()
    game.run()
