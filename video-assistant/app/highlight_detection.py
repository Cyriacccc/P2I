import numpy as np
from app.utils import moving_average, merge_close_segments

# Détection des moments forts basés sur le score fusionné
def detect_highlights(combined_array, fps, k_video_highlight=0.7, min_duration_seconds=0.5):
    # Lissage du signal pour réduire le bruit et éviter les faux pics
    smoothed_motion = moving_average(combined_array, window_size=7)

    # Calcul d'un seuil dynamique basé sur la moyenne et l'écart-type du signal lissé
    dynamic_threshold = np.mean(smoothed_motion) + k_video_highlight * np.std(smoothed_motion)

    # Récupération des frames dont le score dépasse le seuil
    high_motion_frames = np.where(smoothed_motion > dynamic_threshold)[0]

    moments = []
    min_duration = int(fps * min_duration_seconds) # durée minimale d'un moment fort en frames

    if len(high_motion_frames) > 0:
        start = high_motion_frames[0]
        prev = start

        # Regroupe les frames consécutives en segments continus
        for frame in high_motion_frames[1:]:
            if frame - prev > 1:
                # Conserve uniquement les segments assez longs pour être considérés comme des moments forts
                if prev - start >= min_duration:
                    segment_score = np.mean(smoothed_motion[start:prev])
                    moments.append((start, prev, segment_score))
                start = frame
            prev = frame
        
        if prev - start >= min_duration:
            segment_score = np.mean(smoothed_motion[start:prev])
            moments.append((start, prev, segment_score))

        # Trie les moments par score décroissant pour prioriser les plus pertinents
        moments = sorted(moments, key=lambda x: x[2], reverse=True)

    return moments, smoothed_motion, dynamic_threshold

# Sélection des meilleurs moments pour le best-of
def select_bestof_segments(
    moments,
    scene_segments,
    fps,
    frame_count,
    min_bestof_ratio=0.2,
    min_moments=5,
    merge_gap_seconds=1.0
):
    video_duration = frame_count / fps
    min_bestof_duration = video_duration * min_bestof_ratio # durée minimale souhaitée pour le best-of

    selected_moments = []
    current_duration = 0

    # 1. Sélection prioritaire des moments forts détectés
    for start, end, score in moments:
        segment_duration = (end - start) / fps

        selected_moments.append((start, end))
        current_duration += segment_duration
        # Arrêt dès que les critères minimums sont atteints
        if len(selected_moments) >= min_moments and current_duration >= min_bestof_duration:
            break

    # 2. Complément avec les segments de scènes si la durée reste insuffisante
    if current_duration < min_bestof_duration:
        for start, end in scene_segments:
            overlap = False

            # Vérifie qu'un segment de scène ne recouvre pas un segment déjà sélectionné
            for sel_start, sel_end in selected_moments:
                if not (end < sel_start or start > sel_end):
                    overlap = True
                    break

            if not overlap:
                selected_moments.append((start, end))
                current_duration += (end - start) / fps

            if current_duration >= min_bestof_duration:
                break

    # 3. Trie les segments dans l'ordre chronologique
    selected_moments = sorted(selected_moments, key=lambda x: x[0])

    # 4. Fusionne les segments très proches pour améliorer la fluidité du montage
    merge_gap_frames = int(merge_gap_seconds * fps)
    selected_moments = merge_close_segments(selected_moments, merge_gap_frames)

    # 5. Recalcul de la durée après fusion
    current_duration = 0
    for start, end in selected_moments:
        current_duration += (end - start) / fps

    return selected_moments, video_duration, min_bestof_duration, current_duration