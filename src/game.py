# Anciens imports dans main.py
from enum import Enum, auto
import json
import os
import math
import random
from dataclasses import dataclass
from typing import List, Dict
import time

# Nouveaux imports dans src/game.py
import pygame
import sys
import json
import os
import math
import random
import time
from typing import List, Dict

from src.constants import *
from src.enums import GameMode, TowerType, MonsterType
from src.entities import Tower, Monster, Explosion
from src.managers import WaveManager, Wave

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
        self.show_speed_debug = False  # Nouveau flag pour le debug de vitesse
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

        self.background = pygame.image.load('src/assets/background.png').convert()
        
        # Chargement et préparation de l'image de terrain
        try:
            self.terrain_image = pygame.image.load("assets/speedmask.png").convert_gray()
            # Mise à l'échelle si nécessaire pour correspondre à WORLD_SIZE
            if self.terrain_image.get_width() != WORLD_SIZE or self.terrain_image.get_height() != WORLD_SIZE:
                self.terrain_image = pygame.transform.scale(self.terrain_image, (WORLD_SIZE, WORLD_SIZE))
        except FileNotFoundError:
            print("Warning: terrain.png not found in assets folder. Using default terrain.")
            self.terrain_image = pygame.Surface((WORLD_SIZE, WORLD_SIZE))
            self.terrain_image.fill((255, 255, 255))  # Terrain blanc par défaut
        
        # Création d'un array numpy pour accès rapide aux pixels
        self.terrain_array = pygame.surfarray.array2d(self.terrain_image)
        
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
        self.wave_manager = WaveManager(self.village_x, self.village_y, self)
        self.game_start_time = time.time()
        self.monsters = []
        
        # Recentrer la caméra sur le village
        self.camera_x = self.village_x
        self.camera_y = self.village_y
        self.zoom = 0.8  # Dézoomer un peu pour voir plus de terrain

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
        """Crée une nouvelle explosion"""
        self.explosions.append(Explosion(x, y, max_radius, EXPLOSION_DURATION, color))

    def handle_input(self):
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Gestion du zoom (disponible dans tous les modes)
                if event.button == 4:  # Molette vers le haut (zoom)
                    world_x, world_y = self.screen_to_world(self.mouse_x, self.mouse_y)
                    self.zoom = min(MAX_ZOOM, self.zoom * 1.1)
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
                elif event.key == pygame.K_s:  # Touche S pour le debug de vitesse
                    self.show_speed_debug = not self.show_speed_debug
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
        # Remplir l'écran en noir
        self.screen.fill(BLACK)

        self.screen.blit(self.background, (0, 0))
        
        # Créer une surface noire pour les lumières (pas transparente)
        light_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        light_surface.fill((0, 0, 0))  # Surface noire pour le blending additif
        
        # Dessiner la grille
        grid_start_x = int(self.camera_x - WINDOW_WIDTH / (2 * self.zoom))
        grid_end_x = int(self.camera_x + WINDOW_WIDTH / (2 * self.zoom))
        grid_start_y = int(self.camera_y - WINDOW_HEIGHT / (2 * self.zoom))
        grid_end_y = int(self.camera_y + WINDOW_HEIGHT / (2 * self.zoom))
        
        grid_start_x = (grid_start_x // GRID_SIZE) * GRID_SIZE
        grid_end_x = (grid_end_x // GRID_SIZE + 1) * GRID_SIZE
        grid_start_y = (grid_start_y // GRID_SIZE) * GRID_SIZE
        grid_end_y = (grid_end_y // GRID_SIZE + 1) * GRID_SIZE
        
        for x in range(grid_start_x, grid_end_x + GRID_SIZE, GRID_SIZE):
            start_pos = self.world_to_screen(x, grid_start_y)
            end_pos = self.world_to_screen(x, grid_end_y)
            pygame.draw.line(self.screen, GRAY, 
                            (int(start_pos[0]), int(start_pos[1])), 
                            (int(end_pos[0]), int(end_pos[1])))
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
        
        # Dessiner les tours
        for tower in self.towers:
            screen_x, screen_y = self.world_to_screen(tower.x, tower.y)
            color = BLUE if tower.tower_type == TowerType.POWERFUL else \
                   GREEN if tower.tower_type == TowerType.MEDIUM else YELLOW
            
            if self.show_ranges:
                range_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                vision_radius = int(tower.vision_range * self.zoom)
                pygame.draw.circle(range_surface, (*color, RANGE_ALPHA//2),
                                 (int(screen_x), int(screen_y)), vision_radius)
                attack_radius = int(tower.attack_range * self.zoom)
                pygame.draw.circle(range_surface, (*color, RANGE_ALPHA),
                                 (int(screen_x), int(screen_y)), attack_radius)
                self.screen.blit(range_surface, (0, 0))
            
            pygame.draw.circle(self.screen, color, 
                             (int(screen_x), int(screen_y)), 
                             int(TOWER_SIZE/2 * self.zoom))
            
            health_ratio = tower.current_health / tower.max_health
            health_width = TOWER_SIZE * self.zoom
            health_height = 5 * self.zoom
            health_x = screen_x - health_width/2
            health_y = screen_y + (TOWER_SIZE/2 + 5) * self.zoom
            
            pygame.draw.rect(self.screen, (64, 64, 64),
                            (health_x, health_y, health_width, health_height))
            pygame.draw.rect(self.screen, (0, 255, 0) if health_ratio > 0.5 else 
                                         (255, 255, 0) if health_ratio > 0.25 else 
                                         (255, 0, 0),
                            (health_x, health_y, health_width * health_ratio, health_height))
            
            if tower == self.selected_tower:
                pygame.draw.circle(self.screen, WHITE, 
                                 (int(screen_x), int(screen_y)), 
                                 int(TOWER_SIZE/2 * self.zoom), 2)

            # Ajouter la lumière de la tour sur la surface de lumière
            if self.game_mode == GameMode.PLAY:
                pygame.draw.circle(light_surface, (20, 20, 20),
                                 (int(screen_x), int(screen_y)),
                                 int(tower.vision_range * self.zoom))
        
        # Dessiner les monstres
        for monster in self.monsters:
            if monster.is_visible(self.village_x, self.village_y, self.towers):
                monster.draw(self.screen, self.camera_x, self.camera_y, self.zoom, 
                           self.show_names, self.show_monster_ranges)
                
                if self.show_debug:
                    debug_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                    monster_screen_x, monster_screen_y = self.world_to_screen(monster.x, monster.y)
                    
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
                    
                    pygame.draw.line(
                        debug_surface,
                        (*monster.color, DEBUG_LINE_ALPHA),
                        (monster_screen_x, monster_screen_y),
                        (target_screen_x, target_screen_y),
                        max(1, int(2 * self.zoom))
                    )
                    
                    circle_color = (255, 255, 0, DEBUG_LINE_ALPHA) if monster.is_fleeing else (*monster.color, DEBUG_LINE_ALPHA)
                    pygame.draw.circle(
                        debug_surface,
                        circle_color,
                        (int(target_screen_x), int(target_screen_y)),
                        int(10 * self.zoom),
                        2
                    )
                    
                    self.screen.blit(debug_surface, (0, 0))
                
                if self.show_speed_debug and monster.is_visible(self.village_x, self.village_y, self.towers):
                    screen_x, screen_y = self.world_to_screen(monster.x, monster.y)
                    multiplier = self.get_terrain_speed_multiplier(monster.x, monster.y)
                    current_speed = monster.speed * multiplier
                    debug_text = f"Speed: {current_speed:.1f} ({multiplier:.2f}x)"
                    font = pygame.font.Font(None, 20)
                    text_surface = font.render(debug_text, True, (255, 255, 0))
                    self.screen.blit(text_surface, (screen_x + 20, screen_y - 20))
        
        # Dessiner les projectiles
        for tower in self.towers:
            for projectile in tower.projectiles:
                projectile.draw(self.screen, self.camera_x, self.camera_y, self.zoom)
        
        # Dessiner les explosions
        for explosion in self.explosions:
            explosion.draw(self.screen, self.camera_x, self.camera_y, self.zoom)
        
        # Gestion des lumières en mode jeu
        if self.game_mode == GameMode.PLAY:
            # Lumière autour du village
            village_screen_x, village_screen_y = self.world_to_screen(self.village_x, self.village_y)
            pygame.draw.circle(light_surface, (30, 30, 30),
                             (int(village_screen_x), int(village_screen_y)),
                             int(LIGHT_MAX_RANGE * self.zoom))
            
            # Lumière active (curseur)
            if self.light_active and self.light_position and self.light_power > 0:
                light_screen_pos = self.world_to_screen(self.light_position[0], self.light_position[1])
                intensity = int(40 * (self.light_power / LIGHT_MAX_POWER))
                pygame.draw.circle(light_surface, (intensity, intensity, intensity),
                                 (int(light_screen_pos[0]), int(light_screen_pos[1])),
                                 int(LIGHT_RADIUS * self.zoom))
            
            # Appliquer la surface de lumière avec le blending additif
            self.screen.blit(light_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            
            # Indicateur de lumière autour du curseur
            mouse_world_pos = self.screen_to_world(self.mouse_x, self.mouse_y)
            is_in_valid_zone = False
            
            dist_to_village = math.sqrt((mouse_world_pos[0] - self.village_x)**2 + 
                                      (mouse_world_pos[1] - self.village_y)**2)
            if dist_to_village <= LIGHT_MAX_RANGE:
                is_in_valid_zone = True
            
            for tower in self.towers:
                dist_to_tower = math.sqrt((mouse_world_pos[0] - tower.x)**2 + 
                                        (mouse_world_pos[1] - tower.y)**2)
                if dist_to_tower <= tower.vision_range:
                    is_in_valid_zone = True
                    break
            
            if is_in_valid_zone and self.light_power > 0:
                cursor_light = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(cursor_light, (255, 255, 200, 30),
                                 (self.mouse_x, self.mouse_y),
                                 int(LIGHT_RADIUS * self.zoom))
                pygame.draw.circle(cursor_light, (255, 255, 200, 100),
                                 (self.mouse_x, self.mouse_y),
                                 int(LIGHT_RADIUS * self.zoom), 2)
                self.screen.blit(cursor_light, (0, 0))
                
                font = pygame.font.Font(None, 20)
                help_text = "Clic droit pour activer la lumière"
                text_surface = font.render(help_text, True, (255, 255, 200))
                self.screen.blit(text_surface, (self.mouse_x + 20, self.mouse_y + 20))
            
            # Barre de puissance de la lumière
            power_ratio = self.light_power / LIGHT_MAX_POWER
            bar_width = 50
            bar_height = 5
            bar_x = self.mouse_x - bar_width/2
            bar_y = self.mouse_y - 20
            
            pygame.draw.rect(self.screen, (64, 64, 64),
                            (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, (255, 255, 200),
                            (bar_x, bar_y, bar_width * power_ratio, bar_height))
        
        # Interface utilisateur
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
                    count_text = str(tower_info['count'])
                    text_surface = pygame.font.Font(None, 24).render(count_text, True, WHITE)
                    self.screen.blit(text_surface, 
                                   (panel_x + TOWER_SIZE//2 - 5, 
                                    WINDOW_HEIGHT - TOWER_PANEL_HEIGHT + TOWER_SIZE + 5))
                panel_x += TOWER_SIZE + 10
            
            button_color = GREEN if self.all_towers_placed() else GRAY
            pygame.draw.rect(self.screen, button_color, self.go_button_rect)
            
            button_text = "GO!" if self.game_mode == GameMode.EDIT else "EDIT"
            font = pygame.font.Font(None, 36)
            text_color = WHITE if self.all_towers_placed() else (128, 128, 128)
            text_surface = font.render(button_text, True, text_color)
            text_rect = text_surface.get_rect(center=self.go_button_rect.center)
            self.screen.blit(text_surface, text_rect)
        
        # Tour en cours de déplacement
        if self.dragged_tower:
            color = BLUE if self.dragged_tower['type'] == TowerType.POWERFUL else \
                   GREEN if self.dragged_tower['type'] == TowerType.MEDIUM else YELLOW
            pygame.draw.circle(self.screen, color, 
                             (self.mouse_x, self.mouse_y), TOWER_SIZE//2)
            
            if self.mouse_y < WINDOW_HEIGHT - TOWER_PANEL_HEIGHT:
                valid = self.is_position_valid(self.mouse_x, self.mouse_y, 
                                            self.dragged_tower.get('existing'))
                pygame.draw.circle(self.screen, WHITE if valid else RED,
                                 (self.mouse_x, self.mouse_y), TOWER_SIZE//2, 2)
        
        # Affichage du mode et de l'accélération
        font = pygame.font.Font(None, 36)
        mode_text = "Mode: " + self.game_mode.name
        text_surface = font.render(mode_text, True, WHITE)
        self.screen.blit(text_surface, (10, 10))
        
        if self.time_accelerated:
            speed_text = f"x{TIME_ACCELERATIONS[self.time_acceleration_index]}"
            text_surface = font.render(speed_text, True, (255, 255, 0))
            self.screen.blit(text_surface, (WINDOW_WIDTH - 60, 10))
        
        # Barre de vie du village
        health_ratio = max(0, self.village_health / VILLAGE_MAX_HEALTH)
        health_width = VILLAGE_HEALTH_BAR_WIDTH * self.zoom
        health_height = 10 * self.zoom
        health_x = village_screen_x - health_width/2
        health_y = village_screen_y - village_radius - health_height - 5
        
        pygame.draw.rect(self.screen, (64, 64, 64),
                        (health_x, health_y, health_width, health_height))
        pygame.draw.rect(self.screen, (0, 255, 0) if health_ratio > 0.5 else 
                                     (255, 255, 0) if health_ratio > 0.25 else 
                                     (255, 0, 0),
                        (health_x, health_y, health_width * health_ratio, health_height))
        
        # Game Over
        if self.game_over:
            font_big = pygame.font.Font(None, 74)
            game_over_text = font_big.render("GAME OVER", True, (255, 0, 0))
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
            self.screen.blit(game_over_text, text_rect)
        
        # Afficher l'image du terrain en mode debug
        if self.show_speed_debug:
            # Créer une surface pour l'overlay du terrain
            terrain_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            
            # Dessiner la portion visible du terrain
            visible_rect = pygame.Rect(
                int(self.camera_x - WINDOW_WIDTH/(2*self.zoom)),
                int(self.camera_y - WINDOW_HEIGHT/(2*self.zoom)),
                int(WINDOW_WIDTH/self.zoom),
                int(WINDOW_HEIGHT/self.zoom)
            )
            
            for x in range(visible_rect.left, visible_rect.right, 10):
                for y in range(visible_rect.top, visible_rect.bottom, 10):
                    multiplier = self.get_terrain_speed_multiplier(x, y)
                    color_value = int(255 * multiplier)
                    screen_x, screen_y = self.world_to_screen(x, y)
                    pygame.draw.circle(terrain_surface, (color_value, color_value, color_value, 64),
                                     (int(screen_x), int(screen_y)), 5)
            
            self.screen.blit(terrain_surface, (0, 0))
        
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

    def get_terrain_speed_multiplier(self, x, y):
        """Calcule le multiplicateur de vitesse basé sur la valeur du pixel du terrain.
        
        Args:
            x (float): Position X dans le monde
            y (float): Position Y dans le monde
            
        Returns:
            float: Multiplicateur de vitesse entre 0.5 (noir) et 1.0 (blanc)
        """
        # Conversion des coordonnées monde en coordonnées image
        terrain_x = int(x * self.terrain_image.get_width() / WORLD_SIZE)
        terrain_y = int(y * self.terrain_image.get_height() / WORLD_SIZE)
        
        # Vérification des limites
        terrain_x = max(0, min(terrain_x, self.terrain_image.get_width() - 1))
        terrain_y = max(0, min(terrain_y, self.terrain_image.get_height() - 1))
        
        # Récupération de la valeur du pixel (0-255)
        try:
            pixel_value = self.terrain_array[terrain_x, terrain_y] & 0xFF
        except IndexError:
            return 1.0  # Valeur par défaut en cas d'erreur
        
        # Conversion en multiplicateur (0.5 pour noir, 1.0 pour blanc)
        return 0.5 + (pixel_value / 255.0) * 0.5


