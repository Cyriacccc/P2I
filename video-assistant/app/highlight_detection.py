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
    merge_gap_seconds=1.0,
    min_bestof_duration=30.0,
    max_bestof_duration=60.0,
):
    video_duration = frame_count / fps

    # Adapter les durées demandées à la durée réelle de la vidéo
    min_duration = min(min_bestof_duration, video_duration)
    max_duration = min(max_bestof_duration, video_duration)

    if min_duration <= 0 or max_duration <= 0:
        raise ValueError("Les durées du Best Of doivent être positives.")

    if min_duration > max_duration:
        raise ValueError(
            "La durée minimale doit être inférieure ou égale "
            "à la durée maximale."
        )

    min_frames = int(min_duration * fps)
    max_frames = int(max_duration * fps)

    selected_moments = []
    current_frames = 0

    # Ajoute un segment sans dépasser la durée maximale
    def add_segment(start, end):
        nonlocal current_frames

        start = max(0, int(start))
        end = min(frame_count, int(end))

        if end <= start:
            return

        remaining_frames = max_frames - current_frames

        if remaining_frames <= 0:
            return

        # Évite de sélectionner plusieurs fois les mêmes images
        for old_start, old_end in selected_moments:
            if not (end <= old_start or start >= old_end):
                return

        segment_length = min(end - start, remaining_frames)

        if segment_length > 0:
            selected_moments.append((start, start + segment_length))
            current_frames += segment_length

    # 1. Sélectionner les moments forts, du meilleur score au moins bon
    for start, end, score in moments:
        if current_frames >= max_frames:
            break

        if (
            len(selected_moments) >= min_moments
            and current_frames >= min_frames
        ):
            break

        add_segment(start, end)

    # 2. Si nécessaire, compléter avec des segments de scènes
    if current_frames < min_frames:
        for start, end in scene_segments:
            if current_frames >= min_frames or current_frames >= max_frames:
                break

            add_segment(start, end)

    # 3. Fusionner les segments proches, sans dépasser le maximum
    selected_moments.sort(key=lambda segment: segment[0])

    merge_gap_frames = int(merge_gap_seconds * fps)
    merged_segments = merge_close_segments(
        selected_moments,
        merge_gap_frames,
    )

    # 4. Contrôler à nouveau la durée après la fusion
    final_segments = []
    remaining_frames = max_frames

    for start, end in merged_segments:
        if remaining_frames <= 0:
            break

        length = min(end - start, remaining_frames)

        if length > 0:
            final_segments.append((start, start + length))
            remaining_frames -= length

    selected_moments = final_segments

    current_duration = sum(
        end - start for start, end in selected_moments
    ) / fps

    print(
        f"Durée demandée : {min_duration:.1f} à "
        f"{max_duration:.1f} secondes"
    )

    if current_duration < min_duration:
        print(
            "⚠️ Impossible d'atteindre la durée minimale avec "
            "les segments disponibles."
        )

    return (
        selected_moments,
        video_duration,
        min_duration,
        current_duration,
    )
