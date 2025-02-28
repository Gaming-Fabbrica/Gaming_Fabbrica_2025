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
from src.score_management import ScoreManager

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Tower Defense")
        self.clock = pygame.time.Clock()
        
        # Suivi de l'état du mode plein écran
        self.is_fullscreen = False
        self.current_width = WINDOW_WIDTH
        self.current_height = WINDOW_HEIGHT
        
        # Initialisation du système audio
        pygame.mixer.init()
        
        # Configuration des sons
        self.sound_volume = 0.5
        self.sound_enabled = True
        self.music_enabled = True
        self.music_volume = 0.1  # Volume plus bas que les effets sonores
        self.voices_enabled = True  # Option pour activer/désactiver les voix
        
        # Chargement des sons
        self.load_sounds()
        
        # Jouer la voix d'introduction
        self.play_voice('intro_voice.mp3')
        
        self.game_mode = GameMode.EDIT
        self.towers = []
        self.projectiles = []
        
        # Initialisation du gestionnaire de scores
        self.score_manager = ScoreManager()
        self.current_score = 0
        self.player_name = "Joueur"
        self.show_leaderboard = False
        self.game_time = 0.0
        
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
        
        # Bouton RESET
        self.reset_button_rect = pygame.Rect(
            WINDOW_WIDTH - GO_BUTTON_WIDTH - 120,  # 110 pixels à gauche du bouton GO
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
        self.light_recharge_delay = LIGHT_RECHARGE_DELAY  # Utiliser la constante
        self.light_recharge_timer = 0.0  # Compte le temps écoulé depuis que la lumière a été déchargée
        self.light_in_cooldown = False    # Indique si la lumière est en période de délai
        self.show_help = False  # Nouvel attribut pour afficher l'aide
        self.show_grid = False  # Nouvel attribut pour afficher/masquer la grille

        self.background = pygame.image.load('src/assets/background.png').convert()

        self.tower_sprites = {}
        self.tower_sprites[TowerType.WEAK] = pygame.image.load('src/assets/tower_weak.png').convert_alpha()
        self.tower_sprites[TowerType.MEDIUM] = pygame.image.load('src/assets/tower_medium.png').convert_alpha()
        self.tower_sprites[TowerType.POWERFUL] = pygame.image.load('src/assets/tower_powerful.png').convert_alpha()

        # Village
        self.village_sprite = pygame.image.load('src/assets/village.png').convert_alpha()

        # Chargement et préparation de l'image de terrain
        try:
            self.speed_mask = pygame.image.load("src/assets/speedmask.png").convert()
            # Mise à l'échelle si nécessaire pour correspondre à WORLD_SIZE
            if self.speed_mask.get_width() != WORLD_SIZE or self.speed_mask.get_height() != WORLD_SIZE:
                self.speed_mask = pygame.transform.scale(self.speed_mask, (WORLD_SIZE, WORLD_SIZE))
        except FileNotFoundError:
            print("Warning: speedmask.png not found in assets folder. Using default speedmask.")
            self.speed_mask = pygame.Surface((WORLD_SIZE, WORLD_SIZE))
            self.speed_mask.fill((255, 255, 255))  # Terrain blanc par défaut
        
        # Création d'un array numpy pour accès rapide aux pixels
        self.terrain_array = pygame.surfarray.array2d(self.speed_mask)
        
        # Charger la sauvegarde si elle existe
        self.load_map()
        
        # Initialisation des sprites des monstres
        self.monster_sprites = self.load_monster_sprites()
        
        # S'assurer que les dimensions actuelles sont correctes
        self.current_width, self.current_height = self.screen.get_size()
        self.update_ui_positions()

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
        
        # Arrêter les voix en cours
        self.stop_voice()
        
        # Recentrer la caméra sur le village
        self.camera_x = self.village_x
        self.camera_y = self.village_y
        self.zoom = 0.8  # Dézoomer un peu pour voir plus de terrain
        
        # Démarrer la musique de fond
        self.play_background_music('background_music.mp3')

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
                    
                    # Vérifier si on clique sur le bouton RESET
                    if self.game_mode == GameMode.EDIT and self.reset_button_rect.collidepoint(self.mouse_x, self.mouse_y):
                        # Remettre les tours dans la barre du bas
                        for tower in self.towers:
                            for tower_info in self.available_towers:
                                if tower_info['type'] == tower.tower_type:
                                    tower_info['count'] += 1
                        self.towers = []  # Vider la liste des tours placées
                        self.selected_tower = None
                        self.play_sound('tower_destroyed')  # Jouer un son pour le feedback
                        return True
                    
                    # Gestion des tours (uniquement en mode EDIT)
                    if self.game_mode == GameMode.EDIT:
                        if self.mouse_y > self.current_height - TOWER_PANEL_HEIGHT:
                            if not self.go_button_rect.collidepoint(self.mouse_x, self.mouse_y):
                                panel_x = 10
                                for tower_info in self.available_towers:
                                    if tower_info['count'] > 0:
                                        tower_rect = pygame.Rect(panel_x, self.current_height - TOWER_PANEL_HEIGHT + 10, 
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
                    
                elif event.button == 3:  # Clic droit
                    # En mode EDIT, le clic droit supprime une tour sélectionnée
                    if self.game_mode == GameMode.EDIT and self.selected_tower:
                        if self.selected_tower in self.towers:
                            self.towers.remove(self.selected_tower)
                            for tower_info in self.available_towers:
                                if tower_info['type'] == self.selected_tower.tower_type:
                                    tower_info['count'] += 1
                            self.play_sound('tower_destroyed')  # Jouer le son de destruction
                            self.selected_tower = None
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Relâchement clic gauche
                    if self.game_mode == GameMode.EDIT and self.dragged_tower:  # Fin du drag & drop d'une tour
                        world_x, world_y = self.screen_to_world(self.mouse_x, self.mouse_y)
                        
                        if self.mouse_y < self.current_height - TOWER_PANEL_HEIGHT and \
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
                elif event.key == pygame.K_h:  # Touche H pour afficher/masquer l'aide
                    self.show_help = not self.show_help
                elif event.key == pygame.K_g:  # Touche G pour afficher/masquer la grille
                    self.show_grid = not self.show_grid
                elif event.key == pygame.K_p:  # Touche P pour couper/activer la musique
                    self.music_enabled = not self.music_enabled
                    if self.music_enabled and self.game_mode == GameMode.PLAY:
                        self.play_background_music('background_music.mp3')
                    else:
                        self.stop_background_music()
                elif event.key == pygame.K_v:  # Touche V pour couper/activer les voix
                    self.voices_enabled = not self.voices_enabled
                    if not self.voices_enabled:
                        # Arrêter toutes les voix en cours si on désactive l'option
                        self.stop_voice()
                elif event.key == pygame.K_F11:  # Touche F11 pour basculer en mode plein écran
                    self.toggle_fullscreen()
                elif event.key == pygame.K_l:  # Touche L pour afficher/masquer le leaderboard
                    self.show_leaderboard = not self.show_leaderboard
                elif event.key == pygame.K_SPACE:  # Touche ESPACE pour recommencer après un game over
                    if self.game_over:
                        self.reset_game()
                        self.show_leaderboard = False
        
        # Déplacement de la carte par drag (disponible dans tous les modes)
        if self.dragging_map and self.last_mouse_pos:
            dx = self.mouse_x - self.last_mouse_pos[0]
            dy = self.mouse_y - self.last_mouse_pos[1]
            self.camera_x -= dx / self.zoom
            self.camera_y -= dy / self.zoom
            self.last_mouse_pos = (self.mouse_x, self.mouse_y)
            
        # Gestion de la lumière avec le clic droit (uniquement en mode PLAY)
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[2] and self.game_mode == GameMode.PLAY:  # Clic droit et uniquement en mode PLAY
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
            
            # Ne pas activer la lumière si la puissance est épuisée ou en délai de recharge
            if is_in_valid_zone and self.light_power > 0 and not self.light_in_cooldown:
                # Jouer le son de la lumière seulement quand elle est activée
                if not self.light_active:
                    self.play_sound('light_on')
                self.light_active = True
                self.light_position = mouse_world_pos
                # Forcer la mise à jour de la position de la lumière pour éviter les problèmes
                print(f"Lumière activée à: {mouse_world_pos}, puissance: {self.light_power}")
            else:
                # Si on était actif mais qu'on ne peut plus l'être (soit hors zone, soit puissance épuisée, soit en délai)
                if self.light_active:
                    self.play_sound('light_off')
                    self.light_active = False
                    self.light_position = None
                    print("Lumière désactivée: hors zone, puissance épuisée ou en délai")
        else:
            # Si on relâche le clic droit ou si on n'est pas en mode PLAY
            if self.light_active:
                self.play_sound('light_off')
                self.light_active = False
                self.light_position = None
                print("Lumière désactivée: clic relâché ou mode non-play")
        
        return True

    def update(self):
        """Mise à jour de la logique du jeu"""
        if self.game_mode == GameMode.PLAY and not self.game_over:
            current_time = time.time() - self.game_start_time
            self.game_time = current_time
            
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
                # Jouer le son quand la tour tire
                if tower.is_firing:
                    self.play_sound('tower_fire')
                    # Ajouter des points pour chaque tir de tour
                    self.current_score += 1
            
            # Mise à jour des monstres et nettoyage des morts
            dead_monsters = [monster for monster in self.monsters if monster.is_dead]
            self.monsters = [monster for monster in self.monsters if not monster.is_dead]
            
            # Jouer le son pour chaque monstre mort
            for dead_monster in dead_monsters:
                self.play_sound('monster_death')
                # Ajouter des points pour chaque monstre tué en fonction de sa difficulté
                score_gain = 0
                if dead_monster.monster_type == MonsterType.SKELETON:
                    score_gain = 10
                elif dead_monster.monster_type == MonsterType.WOLF:
                    score_gain = 15
                elif dead_monster.monster_type == MonsterType.MORAY:
                    score_gain = 20
                elif dead_monster.monster_type == MonsterType.FIRE_SKELETON:
                    score_gain = 25
                elif dead_monster.monster_type == MonsterType.SMALL_SPIRIT:
                    score_gain = 30
                elif dead_monster.monster_type == MonsterType.WITCH:
                    score_gain = 40
                elif dead_monster.monster_type == MonsterType.KAMIKAZE:
                    score_gain = 35
                elif dead_monster.monster_type == MonsterType.GIANT_WOLF:
                    score_gain = 50
                elif dead_monster.monster_type == MonsterType.DRAGON:
                    score_gain = 100
                else:
                    score_gain = 10
                
                self.current_score += score_gain
            
            for monster in self.monsters:
                # Ne passer la lumière active aux monstres que si sa puissance est supérieure à 0
                light_active_for_monster = self.light_active and self.light_power > 0
                
                # Ne pas ajuster la puissance de la lumière en fonction du zoom pour les monstres
                # Le zoom ne devrait affecter que le rendu visuel, pas la logique du jeu
                monster.update(self.towers, self.village_x, self.village_y, delta_time,
                             self.light_position, light_active_for_monster, self.light_power)
                
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
                            self.play_sound('tower_destroyed')  # Jouer le son de destruction
                            # Perdre des points quand une tour est détruite
                            self.current_score = max(0, self.current_score - 50)
                
                elif monster.current_target_type == 'village':
                    dist = math.sqrt((self.village_x - monster.x)**2 + 
                                   (self.village_y - monster.y)**2)
                    
                    if dist < VILLAGE_SIZE:  # Si le monstre est assez proche du village
                        # Infliger des dégâts au village
                        self.village_health -= monster.current_damage * delta_time * monster.attack_speed
                        # Perdre des points quand le village subit des dégâts
                        self.current_score = max(0, self.current_score - int(monster.current_damage * delta_time * monster.attack_speed))
                        
                        if self.village_health <= 0:
                            self.game_over = True
                            self.play_sound('game_over')  # Jouer le son de game over
                            # Gérer le score final et vérifier s'il s'agit d'un high score
                            self.handle_game_over()

            # Mise à jour des explosions
            self.explosions = [exp for exp in self.explosions if not exp.finished]
            for explosion in self.explosions:
                explosion.update(delta_time)

            # Mise à jour de la puissance de la lumière
            if self.light_active:
                self.light_power = max(0, self.light_power - LIGHT_DRAIN_RATE * delta_time)
                # Désactiver automatiquement la lumière si la puissance atteint zéro
                if self.light_power <= 0:
                    self.light_active = False
                    self.light_position = None
                    self.light_in_cooldown = True  # Activer le délai de recharge
                    self.light_recharge_timer = 0.0  # Réinitialiser le timer
                    self.play_sound('light_off')  # Jouer un son quand la lumière s'éteint automatiquement
            else:
                # Gestion du délai de recharge
                if self.light_in_cooldown:
                    self.light_recharge_timer += delta_time
                    if self.light_recharge_timer >= self.light_recharge_delay:
                        self.light_in_cooldown = False  # Fin du délai de recharge
                else:
                    # Recharge normale seulement si on n'est pas en délai
                    self.light_power = min(LIGHT_MAX_POWER, self.light_power + LIGHT_RECHARGE_RATE * delta_time)

    def draw(self):
        # Remplir l'écran en noir
        self.screen.fill(BLACK)

        # Calculer la taille et la position du fond en fonction du zoom
        background_width = int(WORLD_SIZE * self.zoom)
        background_height = int(WORLD_SIZE * self.zoom)
        
        # Calculer la position du fond pour qu'il soit centré sur la caméra
        background_x, background_y = self.world_to_screen(0, 0)
        
        # Redimensionner et positionner l'image de fond
        scaled_background = pygame.transform.scale(self.background, (background_width, background_height))
        self.screen.blit(scaled_background, (background_x, background_y))
        
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
        
        if self.show_grid:
            for x in range(grid_start_x, grid_end_x + GRID_SIZE, GRID_SIZE):
                start_pos = self.world_to_screen(x, grid_start_y)
                end_pos = self.world_to_screen(x, grid_end_y)
                pygame.draw.line(self.screen, GRAY, 
                               (int(start_pos[0]), int(start_pos[1])), 
                               (int(end_pos[0]), int(end_pos[1])))
        
        # Dessiner le village
        village_screen_x, village_screen_y = self.world_to_screen(self.village_x, self.village_y)
        village_radius = int(VILLAGE_SIZE/2 * self.zoom)
        # pygame.draw.circle(self.screen, RED, (int(village_screen_x), int(village_screen_y)), village_radius)

        # Dessiner le village (image)
        self.screen.blit(
            pygame.transform.scale(self.village_sprite, (int(VILLAGE_SIZE * self.zoom), int(VILLAGE_SIZE * self.zoom))),
            (village_screen_x - VILLAGE_SIZE/2*self.zoom, village_screen_y - VILLAGE_SIZE/2*self.zoom)
        )
        
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
            
            self.screen.blit(pygame.transform.scale(self.tower_sprites[tower.tower_type], (int(TOWER_SIZE * self.zoom), int(TOWER_SIZE * self.zoom))), (screen_x - TOWER_SIZE/2*self.zoom, screen_y - TOWER_SIZE/2*self.zoom))
            
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
            village_light_radius = int(LIGHT_MAX_RANGE * self.zoom)
            pygame.draw.circle(light_surface, (30, 30, 30),
                             (int(village_screen_x), int(village_screen_y)),
                              village_light_radius)
            
            # Lumière active (curseur)
            if self.light_active and self.light_position and self.light_power > 0:
                light_screen_pos = self.world_to_screen(self.light_position[0], self.light_position[1])
                intensity = int(60 * (self.light_power / LIGHT_MAX_POWER))  # Augmenter l'intensité
                # S'assurer que le rayon de la lumière est correctement ajusté par le zoom
                light_radius = int(LIGHT_RADIUS * self.zoom)
                # Dessiner un cercle plus lumineux avec une intensité accrue
                pygame.draw.circle(light_surface, (intensity, intensity, intensity),
                                 (int(light_screen_pos[0]), int(light_screen_pos[1])),
                                 light_radius)
                # Ajouter un second cercle plus petit et plus intense pour un effet de halo
                inner_radius = int(light_radius * 0.6)
                inner_intensity = min(255, int(intensity * 1.5))
                pygame.draw.circle(light_surface, (inner_intensity, inner_intensity, inner_intensity),
                                 (int(light_screen_pos[0]), int(light_screen_pos[1])),
                                 inner_radius)
            
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
            
            # N'afficher l'indicateur de lumière que si la zone est valide ET que la puissance est > 0
            if is_in_valid_zone and self.light_power > 0:
                cursor_light = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                # Ajuster la taille de l'indicateur en fonction du zoom pour correspondre à la vraie zone d'effet
                cursor_light_radius = int(LIGHT_RADIUS * self.zoom)
                
                # Effet de pulsation basé sur le temps
                pulse = (math.sin(pygame.time.get_ticks() / 300) + 1) * 0.3 + 0.4  # Valeur entre 0.4 et 1.0
                
                # Cercle extérieur pulsant
                alpha_outer = int(30 * pulse)
                pygame.draw.circle(cursor_light, (255, 255, 200, alpha_outer),
                                 (self.mouse_x, self.mouse_y),
                                 cursor_light_radius)
                
                # Bordure plus visible avec pulsation
                border_width = max(1, int(3 * self.zoom * pulse))
                alpha_border = int(150 * pulse)
                pygame.draw.circle(cursor_light, (255, 255, 200, alpha_border),
                                 (self.mouse_x, self.mouse_y),
                                 cursor_light_radius, border_width)
                
                # Cercle intérieur pour indiquer l'intensité et la concentration
                inner_radius = int(cursor_light_radius * 0.3 * (self.light_power / LIGHT_MAX_POWER))
                pygame.draw.circle(cursor_light, (255, 255, 150, 40),
                                 (self.mouse_x, self.mouse_y),
                                 inner_radius)
                
                # Appliquer la surface
                self.screen.blit(cursor_light, (0, 0))
                
                # Afficher texte d'aide seulement si non cooldown
                if not self.light_in_cooldown:
                    font = pygame.font.Font(None, 20)
                    help_text = "Clic droit pour activer la lumière"
                    text_surface = font.render(help_text, True, (255, 255, 200))
                    self.screen.blit(text_surface, (self.mouse_x + 20, self.mouse_y + 20))
            
            # Barre de puissance de la lumière (toujours affichée mais rouge si vide)
            power_ratio = self.light_power / LIGHT_MAX_POWER
            bar_width = 50
            bar_height = 5
            bar_x = self.mouse_x - bar_width/2
            bar_y = self.mouse_y - 20
            
            pygame.draw.rect(self.screen, (64, 64, 64),
                            (bar_x, bar_y, bar_width, bar_height))
            
            # Couleur de la barre en fonction de l'état : 
            # - Bleu clair pendant la recharge normale
            # - Rouge si épuisée 
            # - Orange pendant le délai de recharge
            if self.light_in_cooldown:
                # Calcul du ratio de progression du délai
                cooldown_ratio = self.light_recharge_timer / self.light_recharge_delay
                pygame.draw.rect(self.screen, (255, 128, 0),
                                (bar_x, bar_y, bar_width * cooldown_ratio, bar_height))
                
                # Afficher un texte de cooldown
                font = pygame.font.Font(None, 20)
                cooldown_text = f"Délai: {self.light_recharge_delay - self.light_recharge_timer:.1f}s"
                text_surface = font.render(cooldown_text, True, (255, 128, 0))
                self.screen.blit(text_surface, (self.mouse_x + 20, self.mouse_y + 20))
            else:
                # Couleur normale ou rouge si épuisée
                bar_color = (100, 200, 255) if self.light_power > 0 else (255, 0, 0)
                pygame.draw.rect(self.screen, bar_color,
                                (bar_x, bar_y, bar_width * power_ratio, bar_height))
                
                # Afficher le texte d'aide pour activer la lumière seulement si la puissance > 0 et non en cooldown
                if is_in_valid_zone and self.light_power > 0:
                    font = pygame.font.Font(None, 20)
                    help_text = "Clic droit pour activer la lumière"
                    text_surface = font.render(help_text, True, (255, 255, 200))
                    self.screen.blit(text_surface, (self.mouse_x + 20, self.mouse_y + 20))
        
        # Interface utilisateur
        if self.game_mode == GameMode.EDIT:
            pygame.draw.rect(self.screen, GRAY, 
                           (0, self.current_height - TOWER_PANEL_HEIGHT, 
                            self.current_width, TOWER_PANEL_HEIGHT))
            
            panel_x = 10
            for tower_info in self.available_towers:
                if tower_info['count'] > 0:
                    # Utiliser le sprite de la tour au lieu d'un cercle
                    scaled_sprite = pygame.transform.scale(self.tower_sprites[tower_info['type']], 
                                                        (TOWER_SIZE, TOWER_SIZE))
                    self.screen.blit(scaled_sprite, 
                                   (panel_x, 
                                    self.current_height - TOWER_PANEL_HEIGHT + (TOWER_PANEL_HEIGHT - TOWER_SIZE) // 2))
                    count_text = str(tower_info['count'])
                    text_surface = pygame.font.Font(None, 24).render(count_text, True, WHITE)
                    self.screen.blit(text_surface, 
                                   (panel_x + TOWER_SIZE//2 - 5, 
                                    self.current_height - TOWER_PANEL_HEIGHT + TOWER_SIZE + 5))
                panel_x += TOWER_SIZE + 10
            
            button_color = GREEN if self.all_towers_placed() else GRAY
            pygame.draw.rect(self.screen, button_color, self.go_button_rect)
            
            button_text = "GO!" if self.game_mode == GameMode.EDIT else "EDIT"
            font = pygame.font.Font(None, 36)
            text_color = WHITE if self.all_towers_placed() else (128, 128, 128)
            text_surface = font.render(button_text, True, text_color)
            text_rect = text_surface.get_rect(center=self.go_button_rect.center)
            self.screen.blit(text_surface, text_rect)
            
            # Dessiner le bouton RESET
            pygame.draw.rect(self.screen, RED, self.reset_button_rect)
            reset_text = "RESET"
            reset_surface = font.render(reset_text, True, WHITE)
            reset_rect = reset_surface.get_rect(center=self.reset_button_rect.center)
            self.screen.blit(reset_surface, reset_rect)
        
        # Tour en cours de déplacement
        if self.dragged_tower:
            # Utiliser le sprite de la tour au lieu d'un cercle
            scaled_sprite = pygame.transform.scale(self.tower_sprites[self.dragged_tower['type']], 
                                                (TOWER_SIZE, TOWER_SIZE))
            self.screen.blit(scaled_sprite, 
                           (self.mouse_x - TOWER_SIZE//2, 
                            self.mouse_y - TOWER_SIZE//2))
            
            if self.mouse_y < self.current_height - TOWER_PANEL_HEIGHT:
                valid = self.is_position_valid(self.mouse_x, self.mouse_y, 
                                            self.dragged_tower.get('existing'))
                # Dessiner un cercle de validation autour de la tour
                pygame.draw.circle(self.screen, WHITE if valid else RED,
                                 (self.mouse_x, self.mouse_y), TOWER_SIZE//2, 2)
        
        # Appeler la méthode draw_ui pour afficher le score et autres informations UI
        self.draw_ui()
        
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
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 100))
            self.screen.blit(game_over_text, text_rect)
            
            score_text = font_big.render(f"Score: {self.current_score}", True, (255, 200, 0))
            score_rect = score_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 30))
            self.screen.blit(score_text, score_rect)
            
            font = pygame.font.Font(None, 36)
            if self.score_manager.is_high_score(self.current_score):
                highscore_text = font.render("Nouveau High Score!", True, (0, 255, 0))
                highscore_rect = highscore_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 + 30))
                self.screen.blit(highscore_text, highscore_rect)
            
            restart_text = font.render("Appuyez sur ESPACE pour recommencer", True, (200, 200, 200))
            restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 + 70))
            self.screen.blit(restart_text, restart_rect)
            
            leaderboard_text = font.render("Appuyez sur L pour voir le leaderboard", True, (200, 200, 200))
            leaderboard_rect = leaderboard_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 + 110))
            self.screen.blit(leaderboard_text, leaderboard_rect)
        
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
        
        # Afficher le leaderboard si nécessaire
        if self.show_leaderboard:
            self.draw_leaderboard()
        
        # Affichage de l'aide (après tout le reste pour qu'elle soit au-dessus)
        if self.show_help:
            help_surface = pygame.Surface((self.current_width - 100, self.current_height - 100), pygame.SRCALPHA)
            help_surface.fill((0, 0, 0, 220))  # Fond semi-transparent
            
            help_texts = [
                "Aide du jeu - Commandes clavier",
                "",
                "H : Afficher/masquer cette aide",
                "R : Afficher/masquer les portées des tours",
                "D : Afficher/masquer les informations de debug",
                "S : Afficher/masquer le debug de vitesse/terrain",
                "N : Afficher/masquer les noms des entités",
                "M : Afficher/masquer les zones d'effet des monstres",
                "G : Afficher/masquer la grille",
                "T : Changer l'accélération du temps",
                "P : Couper/activer la musique",
                "V : Couper/activer les voix",
                "L : Afficher le leaderboard",
                "F11 : Basculer en mode plein écran",
                "",
                "Commandes souris:",
                "Clic gauche : Placer/déplacer les tours (mode EDIT)",
                "Clic droit : Supprimer une tour sélectionnée (mode EDIT) / Activer la lumière (mode PLAY)",
                "Clic milieu/molette : Déplacer la carte",
                "Molette haut/bas : Zoomer/dézoomer"
            ]
            
            font = pygame.font.Font(None, 28)
            title_font = pygame.font.Font(None, 36)
            
            y_offset = 20
            
            # Titre
            title_text = title_font.render(help_texts[0], True, (255, 255, 200))
            title_rect = title_text.get_rect(center=(help_surface.get_width() // 2, y_offset + 10))
            help_surface.blit(title_text, title_rect)
            y_offset += 50
            
            # Corps de l'aide
            for i in range(1, len(help_texts)):
                if help_texts[i] == "":
                    y_offset += 20
                    continue
                    
                text_surface = font.render(help_texts[i], True, (220, 220, 220))
                help_surface.blit(text_surface, (30, y_offset))
                y_offset += 30
            
            # Instructions pour fermer
            close_text = font.render("Appuyez sur H pour fermer", True, (255, 200, 200))
            close_rect = close_text.get_rect(center=(help_surface.get_width() // 2, help_surface.get_height() - 30))
            help_surface.blit(close_text, close_rect)
            
            # Dessiner le panneau d'aide centré
            help_rect = help_surface.get_rect(center=(self.current_width // 2, self.current_height // 2))
            self.screen.blit(help_surface, help_rect)
            
            # Bordure
            pygame.draw.rect(self.screen, (200, 200, 200), help_rect, 2)
        
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
        terrain_x = int(x * self.speed_mask.get_width() / WORLD_SIZE)
        terrain_y = int(y * self.speed_mask.get_height() / WORLD_SIZE)
        
        # Vérification des limites
        terrain_x = max(0, min(terrain_x, self.speed_mask.get_width() - 1))
        terrain_y = max(0, min(terrain_y, self.speed_mask.get_height() - 1))
        
        # Récupération de la valeur du pixel (0-255)
        try:
            pixel_value = self.terrain_array[terrain_x, terrain_y] & 0xFF
        except IndexError:
            return 1.0  # Valeur par défaut en cas d'erreur
        
        # Conversion en multiplicateur (0.5 pour noir, 1.0 pour blanc)
        return 0.5 + (pixel_value / 255.0) * 0.5

    def load_sounds(self):
        """Charge tous les effets sonores du jeu"""
        # Vérifier que les dossiers de sons existent, sinon les créer
        sounds_dir = os.path.join('src', 'assets', 'sounds')
        voices_dir = os.path.join('src', 'assets', 'voices')
        music_dir = os.path.join('src', 'assets', 'music')
        
        for directory in [sounds_dir, voices_dir, music_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Dossier créé: {directory}")
        
        self.sounds = {
            'tower_fire': self.load_sound('tower_attack.wav'),
            'monster_death': self.load_sound('monster_death.wav'),
            'tower_destroyed': self.load_sound('tower_destroyed.wav'),
            'light_on': self.load_sound('light_on.wav'),
            'light_off': self.load_sound('light_off.wav'),
            'game_over': self.load_sound('game_over.wav')
        }
        
        # Chargement des fichiers vocaux
        self.voice_sounds = {}
        voice_files = [
            'intro_voice.mp3'
            # Ajoutez d'autres fichiers vocaux ici si nécessaire
        ]
        
        for voice_file in voice_files:
            self.voice_sounds[voice_file] = self.load_voice(voice_file)
        
        # Volume des effets sonores (entre 0.0 et 1.0)
        self.sound_volume = 0.5
        self.sound_enabled = True

    def load_sound(self, filename):
        """Charge un fichier son avec gestion d'erreur"""
        try:
            sound_path = os.path.join('src', 'assets', 'sounds', filename)
            
            # Vérifier si le fichier existe
            if not os.path.exists(sound_path):
                print(f"Fichier son manquant: {filename}. Création d'un son vide...")
                # Créer un son vide si le fichier n'existe pas
                dummy_sound = pygame.mixer.Sound(buffer=bytearray([0, 0, 0, 0]))
                return dummy_sound
                
            sound = pygame.mixer.Sound(sound_path)
            return sound
        except Exception as e:
            print(f"Impossible de charger le son: {filename}. Erreur: {e}")
            # Créer un son vide en cas d'erreur
            try:
                dummy_sound = pygame.mixer.Sound(buffer=bytearray([0, 0, 0, 0]))
                return dummy_sound
            except:
                print("Impossible de créer un son de remplacement.")
                return None
            
    def load_voice(self, filename):
        """Charge un fichier vocal avec gestion d'erreur"""
        try:
            voice_path = os.path.join('src', 'assets', 'voices', filename)
            
            # Vérifier si le fichier existe
            if not os.path.exists(voice_path):
                print(f"Fichier vocal manquant: {filename}. Création d'un son vide...")
                # Vérifier si le dossier existe, sinon le créer
                voice_dir = os.path.join('src', 'assets', 'voices')
                if not os.path.exists(voice_dir):
                    os.makedirs(voice_dir)
                    print(f"Dossier créé: {voice_dir}")
                
                # Créer un son vide
                dummy_sound = pygame.mixer.Sound(buffer=bytearray([0, 0, 0, 0]))
                return dummy_sound
                
            voice = pygame.mixer.Sound(voice_path)
            return voice
        except Exception as e:
            print(f"Impossible de charger le fichier vocal: {filename}. Erreur: {e}")
            # Créer un son vide en cas d'erreur
            try:
                dummy_sound = pygame.mixer.Sound(buffer=bytearray([0, 0, 0, 0]))
                return dummy_sound
            except:
                print("Impossible de créer un son vocal de remplacement.")
                return None

    def play_sound(self, sound_name):
        """Joue un son s'il est disponible et que le son est activé"""
        if self.sound_enabled and sound_name in self.sounds and self.sounds[sound_name]:
            # Vérifier si le son est déjà en cours de lecture
            if self.sounds[sound_name].get_num_channels() == 0:
                self.sounds[sound_name].set_volume(self.sound_volume)
                self.sounds[sound_name].play()

    def play_background_music(self, filename):
        """Charge et joue la musique de fond en boucle"""
        if not self.music_enabled:
            return
            
        try:
            music_path = os.path.join('src', 'assets', 'music', filename)
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)  # -1 indique de jouer en boucle indéfiniment
        except Exception as e:
            print(f"Impossible de charger ou jouer la musique: {filename}. Erreur: {e}")
    
    def play_voice(self, filename):
        """Joue un fichier vocal une seule fois"""
        if not self.sound_enabled or not self.voices_enabled:
            return
            
        # Vérifier si le son vocal est préchargé
        if filename in self.voice_sounds and self.voice_sounds[filename]:
            # Vérifier si le son est déjà en cours de lecture
            if self.voice_sounds[filename].get_num_channels() == 0:
                self.voice_sounds[filename].set_volume(self.sound_volume)
                self.voice_sounds[filename].play()
            return
            
        # Sinon, essayer de charger et jouer à la volée (fallback)
        try:
            voice_path = os.path.join('src', 'assets', 'voices', filename)
            voice = pygame.mixer.Sound(voice_path)
            voice.set_volume(self.sound_volume)
            voice.play()
        except Exception as e:
            print(f"Impossible de charger ou jouer le fichier vocal: {filename}. Erreur: {e}")
    
    def stop_background_music(self):
        """Arrête la musique de fond en cours"""
        pygame.mixer.music.stop()

    def stop_voice(self):
        """Arrête toutes les voix en cours de lecture"""
        # Arrêter toutes les voix préchargées
        for voice_name, voice in self.voice_sounds.items():
            if voice and voice.get_num_channels() > 0:
                voice.stop()

    def load_monster_sprites(self):
        """Charge les sprites pour chaque type de monstre"""
        sprites = {}
        sprite_dir = os.path.join('src', 'assets', 'monsters')
        
        # Vérifier si le dossier existe
        if not os.path.exists(sprite_dir):
            os.makedirs(sprite_dir)
            print(f"Dossier créé: {sprite_dir}")
            print("Veuillez y ajouter des sprites pour les monstres.")
        
        # Charger les sprites pour chaque type de monstre
        for monster_type in MonsterType:
            sprite_path = os.path.join(sprite_dir, f"{monster_type.name.lower()}.png")
            try:
                sprite = pygame.image.load(sprite_path).convert_alpha()
                sprites[monster_type] = sprite
            except:
                # Créer un sprite par défaut pour ce type de monstre
                print(f"Sprite non trouvé pour {monster_type.name}, utilisation d'un sprite par défaut")
                default_sprite = pygame.Surface((MONSTER_SIZE, MONSTER_SIZE), pygame.SRCALPHA)
                
                # Dessiner une forme simple comme sprite par défaut (cercle coloré)
                if monster_type == MonsterType.SKELETON:
                    color = (200, 200, 200)  # Gris clair pour les squelettes
                elif monster_type == MonsterType.WOLF:
                    color = (100, 100, 150)  # Bleu-gris pour les loups
                elif monster_type == MonsterType.MORAY:
                    color = (0, 100, 100)    # Cyan foncé pour les murènes
                elif monster_type == MonsterType.SMALL_SPIRIT:
                    color = (200, 200, 255)  # Bleu clair pour les fantômes
                elif monster_type == MonsterType.FIRE_SKELETON:
                    color = (255, 100, 0)    # Orange pour les squelettes de feu
                elif monster_type == MonsterType.WITCH:
                    color = (128, 0, 128)    # Violet pour les sorcières
                elif monster_type == MonsterType.KAMIKAZE:
                    color = (255, 0, 0)      # Rouge pour les kamikazes
                elif monster_type == MonsterType.GIANT_WOLF:
                    color = (50, 50, 150)    # Bleu foncé pour les loups géants
                elif monster_type == MonsterType.DRAGON:
                    color = (150, 0, 0)      # Rouge foncé pour les dragons
                else:
                    color = (100, 100, 100)  # Gris par défaut
                    
                pygame.draw.circle(default_sprite, color, 
                                (MONSTER_SIZE//2, MONSTER_SIZE//2), 
                                MONSTER_SIZE//2)
                sprites[monster_type] = default_sprite
        
        return sprites

    def toggle_fullscreen(self):
        """Bascule entre le mode plein écran et le mode fenêtré"""
        self.is_fullscreen = not self.is_fullscreen
        
        if self.is_fullscreen:
            # Sauvegarder la taille de la fenêtre actuelle avant de passer en plein écran
            self.windowed_size = self.screen.get_size()
            # Passer en mode plein écran
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            # Revenir au mode fenêtré avec la taille précédente
            self.screen = pygame.display.set_mode(
                (WINDOW_WIDTH, WINDOW_HEIGHT)
            )
        
        # Mettre à jour la taille actuelle
        self.current_width, self.current_height = self.screen.get_size()
        # Mettre à jour les positions des éléments d'interface
        self.update_ui_positions()

    def update_ui_positions(self):
        """Recalcule les positions des éléments d'interface en fonction de la taille d'écran actuelle"""
        # Mettre à jour la position du bouton GO
        self.go_button_rect = pygame.Rect(
            self.current_width - GO_BUTTON_WIDTH - 10,
            self.current_height - TOWER_PANEL_HEIGHT + (TOWER_PANEL_HEIGHT - GO_BUTTON_HEIGHT) // 2,
            GO_BUTTON_WIDTH,
            GO_BUTTON_HEIGHT
        )
        
        # Mettre à jour la position du bouton RESET
        self.reset_button_rect = pygame.Rect(
            self.current_width - GO_BUTTON_WIDTH - 120,  # 110 pixels à gauche du bouton GO
            self.current_height - TOWER_PANEL_HEIGHT + (TOWER_PANEL_HEIGHT - GO_BUTTON_HEIGHT) // 2,
            GO_BUTTON_WIDTH,
            GO_BUTTON_HEIGHT
        )
        
        # Mettre à jour les autres éléments de l'interface si nécessaire
        # Point central de l'écran pour le zoom
        self.center_x = self.current_width // 2
        self.center_y = self.current_height // 2

    def reset_game(self):
        """Réinitialise le jeu pour une nouvelle partie"""
        self.game_mode = GameMode.EDIT
        self.game_over = False
        self.village_health = VILLAGE_MAX_HEALTH
        self.towers = []
        self.monsters = []
        self.explosions = []
        self.current_score = 0
        self.game_time = 0.0
        
        # Réinitialiser les tours disponibles
        self.available_towers = [
            {'type': TowerType.POWERFUL, 'count': 1, 'color': BLUE},    # 1 tour puissante
            {'type': TowerType.MEDIUM, 'count': 2, 'color': GREEN},     # 2 tours moyennes
            {'type': TowerType.WEAK, 'count': 3, 'color': YELLOW}       # 3 tours faibles
        ]
        
        # Réinitialiser la puissance de la lumière
        self.light_power = LIGHT_MAX_POWER
        self.light_active = False
        self.light_position = None
        self.light_in_cooldown = False
        
        # Arrêter les sons en cours
        self.stop_voice()
        self.stop_background_music()
        
        # Recentrer la caméra sur le village
        self.camera_x = self.village_x
        self.camera_y = self.village_y
        self.zoom = 1.0

    def handle_game_over(self):
        """Gère la fin de partie et l'enregistrement des scores"""
        # Vérifier si le score est un high score
        waves_completed = self.wave_manager.current_wave if self.wave_manager else 0
        
        if self.score_manager.is_high_score(self.current_score):
            # Afficher une boîte de dialogue pour entrer son nom
            # Comme nous ne pouvons pas facilement créer des boîtes de dialogue dans Pygame,
            # nous utiliserons un nom par défaut pour l'instant
            self.score_manager.add_score(self.player_name, self.current_score, self.game_time, waves_completed)
            self.show_leaderboard = True
        else:
            # Afficher le score final
            self.show_leaderboard = True

    def draw_ui(self):
        """Dessine l'interface utilisateur"""
        font = pygame.font.Font(None, 36)
        
        # Affichage du mode et de l'accélération
        mode_text = "Mode: " + self.game_mode.name
        text_surface = font.render(mode_text, True, WHITE)
        self.screen.blit(text_surface, (10, 10))
        
        if self.time_accelerated:
            speed_text = f"x{TIME_ACCELERATIONS[self.time_acceleration_index]}"
            text_surface = font.render(speed_text, True, (255, 255, 0))
            self.screen.blit(text_surface, (self.current_width - 60, 10))
        
        # Affichage du score et du temps en mode jeu
        if self.game_mode == GameMode.PLAY:
            minutes = int(self.game_time // 60)
            seconds = int(self.game_time % 60)
            time_str = f"Temps: {minutes:02d}:{seconds:02d}"
            score_str = f"Score: {self.current_score}"
            
            if self.wave_manager is not None:
                wave_str = f"Vague: {self.wave_manager.current_wave + 1}"  # +1 pour affichage plus intuitif
            else:
                wave_str = "Vague: --"
                
            time_surface = font.render(time_str, True, WHITE)
            score_surface = font.render(score_str, True, WHITE)
            wave_surface = font.render(wave_str, True, WHITE)
            
            self.screen.blit(time_surface, (10, 50))
            self.screen.blit(score_surface, (10, 90))
            self.screen.blit(wave_surface, (10, 130))
        
        # Affichage du leaderboard si nécessaire
        if self.show_leaderboard:
            self.draw_leaderboard()

    def draw_leaderboard(self):
        """Affiche le tableau des meilleurs scores"""
        leaderboard_surface = pygame.Surface((self.current_width - 200, self.current_height - 200), pygame.SRCALPHA)
        leaderboard_surface.fill((0, 0, 0, 220))  # Fond semi-transparent
        
        title_font = pygame.font.Font(None, 48)
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
        
        title_text = "Meilleurs Scores"
        title_surface = title_font.render(title_text, True, (255, 255, 200))
        title_rect = title_surface.get_rect(center=(leaderboard_surface.get_width() // 2, 40))
        leaderboard_surface.blit(title_surface, title_rect)
        
        leaderboard = self.score_manager.get_leaderboard()
        y_offset = 100
        
        # En-têtes
        headers = ["Rang", "Joueur", "Score", "Temps", "Vagues"]
        x_positions = [50, 120, 300, 400, 500]
        
        for i, entry in enumerate(leaderboard):
            rank_surface = font.render(f"{i+1}", True, (220, 220, 220))
            name_surface = font.render(entry["player_name"], True, (220, 220, 220))
            score_surface = font.render(f"{entry['score']}", True, (220, 220, 220))
            
            time_str = self.score_manager.format_time(entry["survived_time"])
            time_surface = font.render(time_str, True, (220, 220, 220))
            
            waves_surface = font.render(f"{entry['waves_completed']}", True, (220, 220, 220))
            
            # Mettre en évidence le score actuel
            if self.game_over and entry["player_name"] == self.player_name and entry["score"] == self.current_score and entry["survived_time"] == self.game_time:
                pygame.draw.rect(leaderboard_surface, (100, 100, 150, 100), 
                               (30, y_offset - 5, leaderboard_surface.get_width() - 60, 40))
            
            leaderboard_surface.blit(rank_surface, (x_positions[0], y_offset))
            leaderboard_surface.blit(name_surface, (x_positions[1], y_offset))
            leaderboard_surface.blit(score_surface, (x_positions[2], y_offset))
            leaderboard_surface.blit(time_surface, (x_positions[3], y_offset))
            leaderboard_surface.blit(waves_surface, (x_positions[4], y_offset))
            
            y_offset += 40
            
            # Limiter l'affichage à 10 scores
            if i >= 9:
                break
        
        # Instructions pour fermer
        instruction_text = "Appuyez sur ESPACE pour recommencer"
        instruction_surface = small_font.render(instruction_text, True, (255, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(leaderboard_surface.get_width() // 2, leaderboard_surface.get_height() - 40))
        leaderboard_surface.blit(instruction_surface, instruction_rect)
        
        # Dessiner le panneau du leaderboard centré
        leaderboard_rect = leaderboard_surface.get_rect(center=(self.current_width // 2, self.current_height // 2))
        self.screen.blit(leaderboard_surface, leaderboard_rect)
        
        # Bordure
        pygame.draw.rect(self.screen, (200, 200, 200), leaderboard_rect, 2)


