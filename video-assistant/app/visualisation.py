
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


# Sauvegarde un graphique du signal de mouvement avec seuil et coupures détectées
def save_motion_plot(output_dir, motion_norm, video_cut_threshold, scene_cuts):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "motion_plot.png"

    plt.figure(figsize=(12, 6))
    plt.plot(motion_norm, label="Motion Score (normalisé)")

    plt.axhline(
        y=video_cut_threshold,
        color="r",
        linestyle="--",
        label="Seuil",
    )

    for cut in scene_cuts:
        plt.axvline(x=cut, color="g", linestyle=":", alpha=0.7)

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
    if len(audio_norm) == 0:
        print("ℹ️ Aucun signal audio : graphique audio ignoré.")
        return

    base_path = Path(base_path)
    base_path.mkdir(parents=True, exist_ok=True)
    audio_plot_path = base_path / "audio_plot.png"

    plt.figure(figsize=(12, 6))
    plt.plot(audio_norm, label="Audio Score")
    plt.axhline(
        y=audio_threshold,
        color="r",
        linestyle="--",
        label="Seuil audio",
    )

    for peak in audio_peaks:
        plt.axvline(x=peak, color="orange", linestyle=":", alpha=0.6)

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
    base_path = Path(base_path)
    base_path.mkdir(parents=True, exist_ok=True)
    combined_plot_path = base_path / "combined_plot.png"

    plt.figure(figsize=(12, 6))
    plt.plot(smoothed_motion, label="Score fusionné lissé")

    plt.axhline(
        y=fusion_highlight_threshold,
        color="r",
        linestyle="--",
        label="Seuil fusionné",
    )

    plt.title("Analyse Fusionnée Audio + Vidéo")
    plt.xlabel("Frame Index")
    plt.ylabel("Score fusionné")
    plt.legend()
    plt.tight_layout()
    plt.savefig(combined_plot_path)
    plt.close()

    print(f"🧠 Graphe fusionné sauvegardé : {combined_plot_path}")
