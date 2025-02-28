from enum import Enum, auto

class GameMode(Enum):
    EDIT = 1
    PLAY = 2
    GAME_OVER = 3

class TowerType(Enum):
    POWERFUL = 1    # Tour puissante
    MEDIUM = 2      # Tour moyenne
    WEAK = 3        # Tour faible

class MonsterType(Enum):
    SKELETON = auto()
    WOLF = auto()
    MORAY = auto()
    VARAN = auto()
    SMALL_SPIRIT = auto()
    FIRE_SKELETON = auto()
    WITCH = auto()
    KAMIKAZE = auto()
    GIANT_WOLF = auto()
    GIANT_SKELETON = auto()
    ROYAL_MORAY = auto()
    DRAGON = auto()

# Noms des monstres pour l'affichage
MONSTER_NAMES = {
    MonsterType.SKELETON: "Squelette",
    MonsterType.WOLF: "Loup",
    MonsterType.MORAY: "Murène",
    MonsterType.VARAN: "Varan",
    MonsterType.SMALL_SPIRIT: "Petit Esprit",
    MonsterType.FIRE_SKELETON: "Squelette de Feu",
    MonsterType.WITCH: "Sorcière",
    MonsterType.KAMIKAZE: "Kamikaze",
    MonsterType.GIANT_WOLF: "Loup Géant",
    MonsterType.GIANT_SKELETON: "Squelette Géant",
    MonsterType.ROYAL_MORAY: "Murène Royale",
    MonsterType.DRAGON: "Dragon"
} 