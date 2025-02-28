# Corsica Game - Tower Defense

Un jeu de tower defense en 2D où vous devez protéger votre village contre des vagues de monstres en utilisant des tours et la lumière comme arme.

## 🎮 Caractéristiques du jeu

- **Système de tours** : Placez stratégiquement des tours pour défendre votre village
- **Gestion de la lumière** : Utilisez la lumière comme arme contre les monstres qui la craignent
- **Terrain dynamique** : Une carte en niveaux de gris influence la vitesse des monstres
  - Zones claires (255, 255, 255) : Vitesse normale
  - Zones sombres (0, 0, 0) : Vitesse réduite
  - Les différentes nuances de gris créent des variations de vitesse
- **Différents types de monstres** :
  - Squelettes
  - Loups
  - Murènes
  - Esprits
  - Squelettes de feu
  - Sorcières
  - Kamikazes
  - Loups géants
  - Dragons
  - Et plus encore...

## 🗺️ Système de terrain

Le jeu utilise une image PNG en niveaux de gris comme carte de terrain :

1. **Format de l'image** :
   - PNG en niveaux de gris
   - Dimensions recommandées : 1024x1024 pixels
   - Nom par défaut : `terrain.png`

2. **Influence sur le gameplay** :
   - Blanc (255) : Vitesse normale des monstres (multiplicateur x1)
   - Noir (0) : Vitesse très réduite (multiplicateur x0.5)
   - Gris : Variation linéaire de la vitesse
   - Exemple : Un gris à 128 donnera un multiplicateur de x0.75

3. **Création de carte** :
   - Utilisez un logiciel d'édition d'image (Photoshop, GIMP, etc.)
   - Créez des chemins plus clairs pour les passages
   - Ajoutez des zones sombres pour créer des ralentissements stratégiques
   - Sauvegardez en PNG dans le dossier `assets/`

## 🛠️ Installation

1. Clonez le repository :
```bash
git clone https://github.com/votre-username/CorsicaGame.git
cd CorsicaGame
```

2. Créez un environnement virtuel Python :
```bash
python -m venv venv
source venv/bin/activate  # Sur Linux/Mac
venv\Scripts\activate     # Sur Windows
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## 🎯 Comment jouer

1. Lancez le jeu :
```bash
python main.py
```

2. Contrôles :
- **Clic gauche** : Placer/déplacer une tour (mode EDIT), déplacer la carte (mode PLAY)
- **Clic droit** : Supprimer une tour (mode EDIT), activer la lumière (mode PLAY)
- **Clic milieu/glisser** : Déplacer la carte
- **Molette souris** : Zoom avant/arrière
- **H** : Afficher/masquer l'aide du jeu
- **R** : Afficher/masquer les portées des tours
- **D** : Afficher/masquer les informations de débogage
- **S** : Afficher/masquer le débogage de vitesse et terrain
- **N** : Afficher/masquer les noms des entités
- **M** : Afficher/masquer les zones d'effet des monstres
- **G** : Afficher/masquer la grille
- **T** : Changer l'accélération du temps (1x, 2x, 4x, 8x)

3. Mécaniques de jeu :
- Placez des tours pour protéger votre village
- Gérez votre énergie lumineuse (barre de lumière)
- Les monstres ont différents comportements et faiblesses
- Certains monstres fuient la lumière, d'autres sont plus résistants
- Les tours ont différentes portées de vision et d'attaque

## 🏗️ Structure du projet

```
CorsicaGame/
├── src/
│   ├── entities/
│   │   ├── monster.py
│   │   ├── tower.py
│   │   ├── projectile.py
│   │   └── explosion.py
│   ├── constants.py
│   ├── enums.py
│   └── game.py
├── main.py
├── requirements.txt
└── README.md
```

## 🎯 Objectifs du jeu

- Survivre aux vagues de monstres
- Protéger le village
- Gérer efficacement vos ressources (tours et lumière)
- Adapter votre stratégie selon les types de monstres

## 🔧 Configuration

Le jeu utilise plusieurs constantes que vous pouvez modifier dans `src/constants.py` :
- Taille de la fenêtre
- Vitesse du jeu
- Statistiques des monstres
- Portée de la lumière
- Et plus encore...

## 🐛 Résolution des problèmes courants

1. **Erreur de pygame non trouvé** :
   - Vérifiez que vous avez bien activé l'environnement virtuel
   - Réinstallez les dépendances : `pip install -r requirements.txt`

2. **Problèmes de performance** :
   - Réduisez le nombre de monstres simultanés
   - Diminuez la qualité des effets lumineux
   - Vérifiez que votre GPU est bien utilisé

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 