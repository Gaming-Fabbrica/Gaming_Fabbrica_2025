# Corsica Game - Tower Defense

Un jeu de tower defense en 2D où vous devez protéger votre village contre des vagues de monstres en utilisant des tours et la lumière comme arme.

## 🎮 Caractéristiques du jeu

- **Système de tours** : Placez stratégiquement des tours pour défendre votre village
- **Gestion de la lumière** : Utilisez la lumière comme arme contre les monstres qui la craignent
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
- **Clic gauche** : Placer une tour
- **Clic droit** : Activer la lumière
- **ZQSD/WASD** : Déplacer la caméra
- **Molette souris** : Zoom avant/arrière
- **Échap** : Menu pause
- **Espace** : Démarrer la partie

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