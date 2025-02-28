# Tower Defense Game

Un jeu de tower defense en 2D développé avec Pygame.

## Installation

1. Cloner le repository :
```bash
git clone [url-du-repo]
cd CorsicaGame
```

2. Créer un environnement virtuel et l'activer :
```bash
python -m venv venv
# Sur Windows
venv\Scripts\activate
# Sur Unix ou MacOS
source venv/bin/activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Lancement du jeu

```bash
python main.py
```

## Contrôles

- **Clic gauche** : Sélectionner/placer une tour
- **Clic droit** : Supprimer une tour (en mode édition) / Utiliser la lumière (en mode jeu)
- **Clic milieu** : Déplacer la caméra
- **Molette** : Zoom avant/arrière
- **R** : Afficher/masquer les portées
- **D** : Afficher/masquer le debug
- **N** : Afficher/masquer les noms des monstres
- **M** : Afficher/masquer les zones d'effet des monstres
- **T** : Changer la vitesse du jeu

## Structure du projet

```
src/
├── constants.py       # Constantes du jeu
├── enums.py          # Énumérations
├── entities/         # Entités du jeu
│   ├── tower.py
│   ├── monster.py
│   ├── projectile.py
│   └── explosion.py
├── managers/         # Gestionnaires
│   └── wave_manager.py
└── game.py          # Classe principale du jeu

main.py              # Point d'entrée
``` 