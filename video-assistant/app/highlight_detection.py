import numpy as np
from app.utils import moving_average, merge_close_segments


def detect_highlights(combined_array, fps, k_video_highlight=0.7, min_duration_seconds=0.5):
    smoothed_motion = moving_average(combined_array, window_size=7)

    dynamic_threshold = np.mean(smoothed_motion) + k_video_highlight * np.std(smoothed_motion)
    high_motion_frames = np.where(smoothed_motion > dynamic_threshold)[0]

    moments = []
    min_duration = int(fps * min_duration_seconds)

    if len(high_motion_frames) > 0:
        start = high_motion_frames[0]
        prev = start

        for frame in high_motion_frames[1:]:
            if frame - prev > 1:
                if prev - start >= min_duration:
                    segment_score = np.mean(smoothed_motion[start:prev])
                    moments.append((start, prev, segment_score))
                start = frame
            prev = frame

        if prev - start >= min_duration:
            segment_score = np.mean(smoothed_motion[start:prev])
            moments.append((start, prev, segment_score))

        moments = sorted(moments, key=lambda x: x[2], reverse=True)

    return moments, smoothed_motion, dynamic_threshold


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
    min_bestof_duration = video_duration * min_bestof_ratio

    selected_moments = []
    current_duration = 0

    # 1. Ajouter d'abord les moments forts
    for start, end, score in moments:
        segment_duration = (end - start) / fps

        selected_moments.append((start, end))
        current_duration += segment_duration

        if len(selected_moments) >= min_moments and current_duration >= min_bestof_duration:
            break

    # 2. Compléter avec les segments issus des coupures de scène
    if current_duration < min_bestof_duration:
        for start, end in scene_segments:
            overlap = False

            for sel_start, sel_end in selected_moments:
                if not (end < sel_start or start > sel_end):
                    overlap = True
                    break

            if not overlap:
                selected_moments.append((start, end))
                current_duration += (end - start) / fps

            if current_duration >= min_bestof_duration:
                break

    # 3. Tri chronologique
    selected_moments = sorted(selected_moments, key=lambda x: x[0])

    # 4. Fusion des segments proches
    merge_gap_frames = int(merge_gap_seconds * fps)
    selected_moments = merge_close_segments(selected_moments, merge_gap_frames)

    # 5. Recalcul de la durée après fusion
    current_duration = 0
    for start, end in selected_moments:
        current_duration += (end - start) / fps

    return selected_moments, video_duration, min_bestof_duration, current_duration