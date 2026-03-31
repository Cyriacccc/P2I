from pathlib import Path
from cv2 import threshold
import matplotlib.pyplot as plt
import numpy as np


def save_motion_plot(base_path, motion_array, threshold, scene_cuts):
    plot_path = base_path / "outputs" / "motion_plot.png"

    plt.figure(figsize=(12, 6))
    motion_norm = (motion_array - np.min(motion_array)) / (np.max(motion_array) - np.min(motion_array))

    threshold_norm = (threshold - np.min(motion_array)) / (np.max(motion_array) - np.min(motion_array))

    plt.plot(motion_norm, label="Motion Score (normalisé)")
    plt.axhline(y=threshold_norm, color='r', linestyle='--', label="Seuil")

    for cut in scene_cuts:
        plt.axvline(x=cut, color='g', linestyle=':', alpha=0.7)

    plt.title("Analyse du Mouvement Vidéo")
    plt.xlabel("Frame Index")
    plt.ylabel("Motion Score")
    plt.legend()

    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    print(f"📈 Graphe sauvegardé : {plot_path}")


def save_audio_plot(base_path, audio_norm, audio_threshold, audio_peaks):
    if len(audio_norm) == 0:
        return

    audio_plot_path = base_path / "outputs" / "audio_plot.png"

    plt.figure(figsize=(12, 6))
    plt.plot(audio_norm, label="Audio Score")
    plt.axhline(y=audio_threshold, color='r', linestyle='--', label="Seuil audio")

    for peak in audio_peaks:
        plt.axvline(x=peak, color='orange', linestyle=':', alpha=0.6)

    plt.title("Analyse Audio")
    plt.xlabel("Frame Index")
    plt.ylabel("Audio Energy (normalisée)")
    plt.legend()

    plt.tight_layout()
    plt.savefig(audio_plot_path)
    plt.close()

    print(f"🔊 Graphe audio sauvegardé : {audio_plot_path}")


def save_combined_plot(base_path, combined_array):
    combined_plot_path = base_path / "outputs" / "combined_plot.png"

    combined_threshold = np.mean(combined_array) + 0.7 * np.std(combined_array)

    plt.figure(figsize=(12, 6))
    plt.plot(combined_array, label="Score fusionné")
    plt.axhline(
        y=combined_threshold,
        color='r',
        linestyle='--',
        label="Seuil fusionné"
    )

    plt.title("Analyse Fusionnée Audio + Vidéo")
    plt.xlabel("Frame Index")
    plt.ylabel("Score fusionné")
    plt.legend()

    plt.tight_layout()
    plt.savefig(combined_plot_path)
    plt.close()

    print(f"🧠 Graphe fusionné sauvegardé : {combined_plot_path}")