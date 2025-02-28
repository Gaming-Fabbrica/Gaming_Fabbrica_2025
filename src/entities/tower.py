import pygame
import math
from ..constants import (
    TOWER_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT, 
    RANGE_ALPHA, BLUE, GREEN, YELLOW
)
from ..enums import TowerType
from .projectile import Projectile

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
        self.is_dead = False
        self.is_firing = False  # Nouvel attribut pour indiquer si la tour est en train de tirer

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
        # Réinitialiser l'état de tir
        self.is_firing = False
        
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
                self.is_firing = True  # La tour est en train de tirer
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

    def draw(self, screen, camera_x, camera_y, zoom, show_ranges=False):
        """Dessine la tour et ses effets"""
        screen_x, screen_y = self.world_to_screen(camera_x, camera_y, zoom)
        
        # Déterminer la couleur de la tour
        color = BLUE if self.tower_type == TowerType.POWERFUL else \
               GREEN if self.tower_type == TowerType.MEDIUM else YELLOW
        
        # Dessiner les zones d'attaque si activé
        if show_ranges:
            range_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            
            # Dessiner le cercle de vision
            vision_radius = int(self.vision_range * zoom)
            pygame.draw.circle(range_surface, (*color, RANGE_ALPHA//2),
                             (int(screen_x), int(screen_y)), vision_radius)
            
            # Dessiner le cercle d'attaque
            attack_radius = int(self.attack_range * zoom)
            pygame.draw.circle(range_surface, (*color, RANGE_ALPHA),
                             (int(screen_x), int(screen_y)), attack_radius)
            
            screen.blit(range_surface, (0, 0))
        
        # Dessiner la tour
        pygame.draw.circle(screen, color, 
                         (int(screen_x), int(screen_y)), 
                         int(TOWER_SIZE/2 * zoom))
        
        # Dessiner la barre de vie
        self.draw_health_bar(screen, screen_x, screen_y, zoom)
        
        # Dessiner les projectiles
        for projectile in self.projectiles:
            projectile.draw(screen, camera_x, camera_y, zoom)

    def draw_health_bar(self, screen, screen_x, screen_y, zoom):
        """Dessine la barre de vie de la tour"""
        health_ratio = self.current_health / self.max_health
        health_width = TOWER_SIZE * zoom
        health_height = 5 * zoom
        health_x = screen_x - health_width/2
        health_y = screen_y + (TOWER_SIZE/2 + 5) * zoom
        
        # Fond de la barre de vie
        pygame.draw.rect(screen, (64, 64, 64),
                        (health_x, health_y, health_width, health_height))
        # Barre de vie actuelle
        health_color = (0, 255, 0) if health_ratio > 0.5 else \
                      (255, 255, 0) if health_ratio > 0.25 else \
                      (255, 0, 0)
        pygame.draw.rect(screen, health_color,
                        (health_x, health_y, health_width * health_ratio, health_height))

    def world_to_screen(self, camera_x, camera_y, zoom):
        """Convertit les coordonnées du monde en coordonnées écran"""
        screen_x = (self.x - camera_x) * zoom + WINDOW_WIDTH/2
        screen_y = (self.y - camera_y) * zoom + WINDOW_HEIGHT/2
        return screen_x, screen_y 