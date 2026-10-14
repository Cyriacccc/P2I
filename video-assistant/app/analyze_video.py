
import csv
from pathlib import Path
import numpy as np

from app.analyze_audio import compute_audio_scores
from app.export import export_best_of
from app.thumbnail import generate_thumbnail
from app.utils import normalize_signal, moving_average
from app.video_analysis import (
    compute_motion_scores,
    detect_scene_cuts,
    build_scene_segments,
)
from app.visualisation import (
    save_motion_plot,
    save_audio_plot,
    save_combined_plot,
)
from app.highlight_detection import detect_highlights, select_bestof_segments


# PARAMÈTRES GLOBAUX

AUDIO_WEIGHT = 0.3
VIDEO_WEIGHT = 0.7

MIN_CUT_GAP_SECONDS = 0.5
MIN_HIGHLIGHT_DURATION_SECONDS = 0.5
MAX_SCENE_DURATION_SECONDS = 3.0
MIN_BESTOF_RATIO = 0.2
MIN_BESTOF_MOMENTS = 5
MERGE_GAP_SECONDS = 1.0

PLOT_WINDOW_SIZE = 7

CSV_FILENAME = "scene_cuts.csv"
THUMBNAIL_FILENAME = "thumbnail.png"


# AFFICHAGE DES STATISTIQUES

def print_video_stats(mean_motion, std_motion, k_video_cut, threshold, scene_cuts):
    print("\n🎬 ANALYSE VIDÉO")
    print(f"Moyenne : {mean_motion:.2f}")
    print(f"Écart-type : {std_motion:.2f}")
    print(f"k_video_cut : {k_video_cut:.2f}")
    print(f"Seuil : {threshold:.2f}")
    print(f"Coupures : {len(scene_cuts)}")


def print_audio_stats(mean_audio, std_audio, k_audio, audio_threshold, audio_peaks):
    print("\n🔊 ANALYSE AUDIO")
    print(f"Moyenne : {mean_audio:.2f}")
    print(f"Écart-type : {std_audio:.2f}")
    print(f"k_audio : {k_audio:.2f}")
    print(f"Seuil : {audio_threshold:.2f}")
    print(f"Pics : {len(audio_peaks)}")


def print_bestof_stats(selected_moments, video_duration, min_bestof_duration, current_duration):
    print("\n🎬 BEST-OF")
    print(f"Segments : {len(selected_moments)}")
    print(f"Durée vidéo : {video_duration:.2f}s")
    print(f"Durée min : {min_bestof_duration:.2f}s")
    print(f"Durée finale : {current_duration:.2f}s")


# EXPORT CSV

def export_scene_cuts_csv(output_dir, scene_cuts, motion_array, fps):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / CSV_FILENAME

    with open(output_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["frame_index", "time_seconds", "motion_score"])

        for index in scene_cuts:
            time_sec = index / fps
            writer.writerow([index, time_sec, motion_array[index]])

    print(f"📄 CSV exporté : {output_path}")


# FONCTION PRINCIPALE

def analyze_video(
    video_path: str,
    k_audio=0.7,
    k_video_cut=2.0,
    k_video_highlight=0.7,
    output_name="best_of.mp4",
    artifacts_dir=None,
):
    # 1. Analyse vidéo
    motion_array, fps, frame_count = compute_motion_scores(video_path)

    if motion_array is None or len(motion_array) == 0:
        raise ValueError("Impossible d'analyser cette vidéo.")

    # 2. Analyse audio
    audio_array = compute_audio_scores(video_path, fps)

    print("Taille motion_array :", len(motion_array))
    print("Taille audio_array :", len(audio_array))

    # 3. Alignement et normalisation des signaux
    if len(audio_array) > 0:
        min_length = min(len(motion_array), len(audio_array))
        motion_array = motion_array[:min_length]
        audio_array = audio_array[:min_length]

        motion_norm = normalize_signal(motion_array)
        audio_norm = normalize_signal(audio_array)

        combined_array = (
            VIDEO_WEIGHT * motion_norm
            + AUDIO_WEIGHT * audio_norm
        )
    else:
        motion_norm = normalize_signal(motion_array)
        audio_norm = np.array([])
        combined_array = motion_norm

    # 4. Statistiques audio
    if len(audio_array) > 0:
        audio_threshold = np.mean(audio_norm) + k_audio * np.std(audio_norm)
        audio_peaks = np.where(audio_norm > audio_threshold)[0]
        mean_audio = np.mean(audio_norm)
        std_audio = np.std(audio_norm)
    else:
        audio_threshold = 0
        audio_peaks = []
        mean_audio = 0
        std_audio = 0

    # 5. Détection des coupures
    mean_motion, std_motion, threshold, scene_cuts = detect_scene_cuts(
        motion_array,
        fps,
        k_video_cut=k_video_cut,
    )

    scene_segments = build_scene_segments(
        scene_cuts,
        fps,
        max_scene_duration=MAX_SCENE_DURATION_SECONDS,
    )

    print("✅ Analyse terminée")
    print_video_stats(
        mean_motion, std_motion, k_video_cut, threshold, scene_cuts
    )
    print_audio_stats(
        mean_audio, std_audio, k_audio, audio_threshold, audio_peaks
    )

    # 6. Export CSV
    base_path = Path(__file__).resolve().parent.parent

    if artifacts_dir is None:
       artifacts_dir = base_path / "outputs"
    else:
       artifacts_dir = Path(artifacts_dir)

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    export_scene_cuts_csv(artifacts_dir, scene_cuts, motion_array, fps)

    # 7. Génération des graphiques
    save_motion_plot(artifacts_dir, motion_norm, threshold, scene_cuts)
    save_audio_plot(artifacts_dir, audio_norm, audio_threshold, audio_peaks)

    smoothed_motion = moving_average(
        combined_array,
        window_size=PLOT_WINDOW_SIZE,
    )
    dynamic_threshold = (
        np.mean(smoothed_motion)
        + k_video_highlight * np.std(smoothed_motion)
    )

    save_combined_plot(artifacts_dir, smoothed_motion, dynamic_threshold)

    # 8. Détection des moments forts
    moments, smoothed_motion, dynamic_threshold = detect_highlights(
        combined_array,
        fps,
        k_video_highlight=k_video_highlight,
        min_duration_seconds=MIN_HIGHLIGHT_DURATION_SECONDS,
    )

    print("\n🧠 ANALYSE FUSION")
    print(f"Seuil : {dynamic_threshold:.2f}")
    print(f"k_highlight : {k_video_highlight:.2f}")

    print("\n🎯 Moments forts :")
    for start, end, score in moments:
        print(f"- {start/fps:.2f}s → {end/fps:.2f}s | {score:.2f}")

    # 9. Sélection des segments du Best Of
    (
        selected_moments,
        video_duration,
        min_bestof_duration,
        current_duration,
    ) = select_bestof_segments(
        moments,
        scene_segments,
        fps,
        frame_count,
        min_bestof_ratio=MIN_BESTOF_RATIO,
        min_moments=MIN_BESTOF_MOMENTS,
        merge_gap_seconds=MERGE_GAP_SECONDS,
    )

    print_bestof_stats(
        selected_moments,
        video_duration,
        min_bestof_duration,
        current_duration,
    )

    # 10. Export du Best Of
    output_path = export_best_of(
        video_path,
        selected_moments,
        output_name=output_name,
    )

    # 11. Génération de la miniature
    if len(moments) > 0:
         generate_thumbnail(
     video_path,
     moments[0],
     motion_array,
     output_dir=artifacts_dir,
)
    else:
        print("⚠️ Pas de miniature (aucun moment fort)")

    # Retourne le chemin du fichier généré au serveur web
    return str(output_path)
