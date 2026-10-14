# Video Assistant — Génération automatique de Best Of vidéo

Video Assistant est un projet Python qui analyse une vidéo afin d'identifier des moments intéressants et de générer automatiquement un Best Of. Le projet comprend une interface Web développée avec Flask.

## Fonctionnalités

- Importation de vidéos depuis une interface Web.
- Analyse des mouvements et détection de scènes.
- Analyse audio et fusion des indicateurs pour sélectionner des moments.
- Génération automatique d'une vidéo Best Of.
- Prévisualisation et téléchargement du résultat.
- Génération de graphiques et d'une miniature.

## Technologies

Python, Flask, OpenCV, NumPy, Pandas, Matplotlib et MoviePy.

## Installation locale

Cloner le dépôt GitHub :

```bash
git clone https://github.com/Cyriacccc/P2I.git
cd P2I/video-assistant
```

Créer et activer un environnement virtuel à la racine du dépôt :

```powershell
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```bash
python -m pip install -r requirements.txt
```

## Lancer l'application Web

Depuis le dossier `video-assistant` :

```bash
python -m app.web
```

Ouvrir ensuite l'adresse suivante dans un navigateur :

http://127.0.0.1:5000

## Utilisation

1. Ouvrir l'interface Web.
2. Importer une vidéo dans un format accepté par l'application.
3. Lancer l'analyse.
4. Prévisualiser puis télécharger le Best Of généré.

La durée du traitement dépend notamment de la durée et de la résolution de la vidéo.

## Structure du projet

- `app/` : code Python, interface Web et modules d'analyse.
- `app/templates/` : pages HTML.
- `app/static/` : fichiers CSS et JavaScript.
- `tests/` : tests automatisés.
- `data/` : données et vidéos de test locales.
- `outputs/` : résultats générés localement.

Les vidéos de test et les résultats générés ne sont pas nécessaires au lancement du projet et ne doivent pas être ajoutés au dépôt public.

## Lancer les tests

Depuis le dossier `video-assistant` :

```bash
python -m pytest -v
```

## Limites

Le temps de traitement dépend des ressources disponibles. Un hébergement public devra être configuré pour gérer les limites de taille des fichiers, la mémoire, la durée des analyses et le stockage temporaire.

## Auteur

Projet étudiant réalisé dans le cadre du P2I à l'ENSC Bordeaux INP.


