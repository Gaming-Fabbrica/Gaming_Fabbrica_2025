class Monster:
    def __init__(self, monster_type, x, y, hp, speed, attack_speed, damage, game):
        self.game = game  # Référence au jeu pour accéder aux sprites
        self.sprite = game.monster_sprites[monster_type]  # Récupérer le sprite correspondant 

    def draw(self, screen, camera_x, camera_y, zoom, show_names=False, show_range=False):
        """Dessine le monstre sur l'écran"""
        if not self.is_visible_flag:
            return
        
        screen_x, screen_y = self.world_to_screen(self.x, self.y, camera_x, camera_y, zoom)
        
        # Dessiner la zone d'effet si demandé
        if show_range:
            range_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            attack_radius = int(self.attack_range * zoom)
            pygame.draw.circle(range_surface, (*self.color, RANGE_ALPHA),
                             (int(screen_x), int(screen_y)), attack_radius)
            screen.blit(range_surface, (0, 0))
        
        # Calculer la taille du sprite en fonction du zoom
        monster_size = int(MONSTER_SIZE * zoom)
        
        # Redimensionner le sprite selon le zoom
        scaled_sprite = pygame.transform.scale(self.sprite, (monster_size, monster_size))
        
        # Position pour centrer le sprite
        sprite_x = int(screen_x - monster_size/2)
        sprite_y = int(screen_y - monster_size/2)
        
        # Dessiner le sprite du monstre
        screen.blit(scaled_sprite, (sprite_x, sprite_y))
        
        # Dessiner la flèche indiquant la direction par dessus le sprite
        if self.dx != 0 or self.dy != 0:
            angle = math.atan2(self.dy, self.dx)
            arrow_length = monster_size * 0.6
            end_x = screen_x + math.cos(angle) * arrow_length/2
            end_y = screen_y + math.sin(angle) * arrow_length/2
            pygame.draw.line(screen, WHITE, 
                           (screen_x, screen_y), 
                           (end_x, end_y), 
                           max(1, int(2 * zoom)))
        
        # Barre de vie
        health_ratio = self.current_health / self.max_health
        health_width = MONSTER_SIZE * zoom
        health_height = 3 * zoom
        health_x = screen_x - health_width/2
        health_y = screen_y + (MONSTER_SIZE/2 + 2) * zoom
        
        pygame.draw.rect(screen, (64, 64, 64),
                       (health_x, health_y, health_width, health_height))
        pygame.draw.rect(screen, (0, 255, 0) if health_ratio > 0.5 else 
                                 (255, 255, 0) if health_ratio > 0.25 else 
                                 (255, 0, 0),
                       (health_x, health_y, health_width * health_ratio, health_height))
        
        # Afficher le nom du monstre si demandé
        if show_names:
            monster_name = self.monster_type.name
            font = pygame.font.Font(None, max(10, int(16 * zoom)))
            text_surface = font.render(monster_name, True, WHITE)
            text_rect = text_surface.get_rect(center=(screen_x, screen_y - (MONSTER_SIZE/2 + 10) * zoom))
            screen.blit(text_surface, text_rect) 