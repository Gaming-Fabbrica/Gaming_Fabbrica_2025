import pygame
import math
from ..constants import PROJECTILE_SPEED, PROJECTILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT

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