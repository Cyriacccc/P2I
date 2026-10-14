from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt




# Sauvegarde un graphique du signal de mouvement avec seuil et coupures détectées
def save_motion_plot(base_path, motion_norm, video_cut_threshold, scene_cuts):
    plot_path = base_path / "outputs" / "motion_plot.png"

    plt.figure(figsize=(12, 6))

    # Courbe du mouvement normalisé
    plt.plot(motion_norm, label="Motion Score (normalisé)")

    # Affichage du seuil de détection
    plt.axhline(
        y=video_cut_threshold,
        color='r',
        linestyle='--',
        label="Seuil"
    )

    # Marquage des coupures de scène
    for cut in scene_cuts:
        plt.axvline(x=cut, color='g', linestyle=':', alpha=0.7)

    # Mise en forme du graphique
    plt.title("Analyse du Mouvement Vidéo")
    plt.xlabel("Frame Index")
    plt.ylabel("Motion Score")
    plt.legend()

    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    print(f"📈 Graphe sauvegardé : {plot_path}")


# Sauvegarde un graphique du signal audio avec seuil et pics détectés
def save_audio_plot(base_path, audio_norm, audio_threshold, audio_peaks):
    # Cas sans signal audio exploitable
    if len(audio_norm) == 0:
        return

    audio_plot_path = base_path / "outputs" / "audio_plot.png"

    plt.figure(figsize=(12, 6))

    # Courbe de l'énergie audio normalisée
    plt.plot(audio_norm, label="Audio Score")

    # Seuil de détection des pics audio
    plt.axhline(y=audio_threshold, color='r', linestyle='--', label="Seuil audio")

    # Marquage des pics audio
    for peak in audio_peaks:
        plt.axvline(x=peak, color='orange', linestyle=':', alpha=0.6)

    # Mise en forme
    plt.title("Analyse Audio")
    plt.xlabel("Frame Index")
    plt.ylabel("Audio Energy (normalisée)")
    plt.legend()

    plt.tight_layout()
    plt.savefig(audio_plot_path)
    plt.close()

    print(f"🔊 Graphe audio sauvegardé : {audio_plot_path}")


# Sauvegarde un graphique du score fusionné (audio + vidéo) avec seuil
def save_combined_plot(base_path, smoothed_motion, fusion_highlight_threshold):
    combined_plot_path = base_path / "outputs" / "combined_plot.png"

    plt.figure(figsize=(12, 6))

    # Courbe du score fusionné (après lissage)
    plt.plot(smoothed_motion, label="Score fusionné lissé")

    # Seuil de détection des moments forts
    plt.axhline(
        y=fusion_highlight_threshold,
        color='r',
        linestyle='--',
        label="Seuil fusionné"
    )

    # Mise en forme
    plt.title("Analyse Fusionnée Audio + Vidéo")
    plt.xlabel("Frame Index")
    plt.ylabel("Score fusionné")
    plt.legend()

    plt.tight_layout()
    plt.savefig(combined_plot_path)
    plt.close()

    print(f"🧠 Graphe fusionné sauvegardé : {combined_plot_path}")