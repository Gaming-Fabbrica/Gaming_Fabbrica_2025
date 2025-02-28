import pygame
from ..constants import WINDOW_WIDTH, WINDOW_HEIGHT

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