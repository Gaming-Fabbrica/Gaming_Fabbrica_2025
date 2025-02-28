import math

# Window and Display
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
GRID_SIZE = 32
FPS = 60

# Game Elements Sizes
TOWER_PANEL_HEIGHT = 100  # Hauteur de la zone des tours en bas
TOWER_SIZE = 80  # Taille des tours
VILLAGE_SIZE = 120  # Taille du village (plus grand que TOWER_SIZE qui est 40)
GO_BUTTON_WIDTH = 80
GO_BUTTON_HEIGHT = 40
MONSTER_SIZE = 40  # Taille des triangles des monstres

# World Settings
WORLD_SIZE = 3000  # Taille du monde en pixels
MIN_SPAWN_DISTANCE = 800  # Distance minimale de spawn du village
MAX_SPAWN_DISTANCE = 1200  # Distance maximale de spawn du village
MAX_ZOOM = 4.0
MIN_ZOOM = 0.5

# Visual Effects
RANGE_ALPHA = 128  # Transparence des cercles de portée (0-255)
DEBUG_LINE_ALPHA = 128  # Transparence des lignes de debug

# Game Mechanics
TIME_ACCELERATIONS = [1.0, 5.0, 10.0, 15.0, 20.0]  # Différents niveaux d'accélération
VILLAGE_MAX_HEALTH = 1000
VILLAGE_HEALTH_BAR_WIDTH = 200  # Largeur de la barre de vie du village

# Projectile Settings
PROJECTILE_SPEED = 400  # Vitesse des projectiles en pixels par seconde
PROJECTILE_SIZE = 6    # Taille des projectiles

# Special Abilities Ranges
HEAL_RANGE = 150  # Portée de soin des sorcières
SPIRIT_BUFF_RANGE = 200  # Portée du buff des esprits
KAMIKAZE_EXPLOSION_RANGE = 100  # Portée de l'explosion des kamikazes
EXPLOSION_DURATION = 0.5  # Durée de l'explosion en secondes
EXPLOSION_MAX_RADIUS = 50  # Rayon maximum de l'explosion

# Light Mechanics
LIGHT_MAX_RANGE = 500  # Distance maximale d'utilisation de la lumière depuis le village
LIGHT_MAX_POWER = 100  # Puissance maximale de la lumière
LIGHT_DRAIN_RATE = 15  # Vitesse de décharge (points par seconde)
LIGHT_RECHARGE_RATE = 5  # Vitesse de recharge (points par seconde) - plus lente que la décharge
LIGHT_RECHARGE_DELAY = 2.0  # Délai en secondes avant que la recharge ne commence après décharge complète
LIGHT_POWER_BAR_WIDTH = 200  # Largeur de la barre de puissance
LIGHT_POWER_BAR_HEIGHT = 15  # Hauteur de la barre de puissance
LIGHT_RADIUS = 200    # Rayon d'effet de la lumière

# Monster Behavior
MONSTER_FEAR_DURATION = 5.0  # Durée pendant laquelle le monstre fuit (en secondes)
MAX_FLEE_TIME = 20.0  # Temps maximum de fuite en secondes
FLEE_DISTANCE_MIN = 300  # Distance minimale de fuite
FLEE_DISTANCE_MAX = 500  # Distance maximale de fuite
FLEE_ANGLE_VARIATION = math.pi / 4  # Variation maximale de l'angle de fuite (±45 degrés)
MAX_VISIBILITY_RANGE = 800  # Distance maximale de visibilité depuis le village

# File Paths
SAVE_FILE = "map_save.json"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Couleurs pour le leaderboard
GOLD = (255, 215, 0)     # Or pour la 1ère place
SILVER = (192, 192, 192) # Argent pour la 2ème place
BRONZE = (205, 127, 50)  # Bronze pour la 3ème place 