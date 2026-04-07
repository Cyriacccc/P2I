from pathlib import Path
from app.analyze_video import analyze_video


# Point d'entrée principal du programme
def main():
    # Chemin de la vidéo à analyser
    video_path = Path("data/samples/test.mp4")

    
    # CONFIGURATION UTILISATEUR - AUDIO
    
    # Choix du niveau de sensibilité audio (impacte le seuil de détection)
    audio_sensitivity = input(
        "Choisissez la sensibilité audio (sensible / equilibree / stricte) : "
    ).strip().lower()

    if audio_sensitivity == "sensible":
        k_audio = 0.4
    elif audio_sensitivity == "stricte":
        k_audio = 1.2
    else:
        # Valeur par défaut : équilibrée
        k_audio = 0.7

    
    # CONFIGURATION UTILISATEUR - VIDÉO
    
    # Choix du niveau de sensibilité vidéo (coupures + moments forts)
    video_sensitivity = input(
        "Choisissez la sensibilité vidéo (sensible / equilibree / stricte) : "
    ).strip().lower()

    if video_sensitivity == "sensible":
        k_video_cut = 1.5
        k_video_highlight = 0.5
    elif video_sensitivity == "stricte":
        k_video_cut = 2.5
        k_video_highlight = 1.0
    else:
        # Valeurs par défaut : équilibrées
        k_video_cut = 2.0
        k_video_highlight = 0.7

    # Affichage récapitulatif des paramètres choisis
    print(f"Sensibilité audio choisie : {audio_sensitivity} | k_audio = {k_audio}")
    print(
        f"Sensibilité vidéo choisie : {video_sensitivity} | "
        f"k_video_cut = {k_video_cut}, k_video_highlight = {k_video_highlight}"
    )

    # Lancement du pipeline principal d'analyse et de génération du best-of
    analyze_video(
        str(video_path),
        k_audio=k_audio,
        k_video_cut=k_video_cut,
        k_video_highlight=k_video_highlight
    )


# Exécution du script uniquement s'il est lancé directement
if __name__ == "__main__":
    main()