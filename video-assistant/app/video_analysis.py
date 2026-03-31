import cv2
import numpy as np


def compute_motion_scores(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la vidéo")
        return None, None, None

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print("📊 Analyse en cours...")
    print(f"Frames totales : {frame_count}")
    print(f"FPS : {fps}")

    ret, prev_frame = cap.read()
    if not ret:
        print("❌ Impossible de lire la première frame")
        cap.release()
        return None, None, None

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    prev_hist = cv2.calcHist([prev_gray], [0], None, [256], [0, 256])
    prev_hist = cv2.normalize(prev_hist, prev_hist).flatten()

    frame_index = 1
    motion_scores = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % 100 == 0:
            progress = frame_index / frame_count * 100
            print(f"Progression : {progress:.1f}%")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()

        diff = cv2.absdiff(prev_gray, gray)
        motion_score = np.mean(diff)

        hist_diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)

        combined_score = motion_score + hist_diff * 50
        motion_scores.append(combined_score)

        prev_hist = hist
        prev_gray = gray
        frame_index += 1

    cap.release()

    motion_array = np.array(motion_scores)
    return motion_array, fps, frame_count


def detect_scene_cuts(motion_array, fps, k_video_cut=2.0):
    mean_motion = np.mean(motion_array)
    std_motion = np.std(motion_array)

    threshold = mean_motion + k_video_cut * std_motion
    raw_cuts = np.where(motion_array > threshold)[0]

    scene_cuts = []
    min_gap = int(fps * 0.5)
    last_cut = -min_gap

    for cut in raw_cuts:
        if cut - last_cut >= min_gap:
            scene_cuts.append(cut)
            last_cut = cut

    return mean_motion, std_motion, threshold, scene_cuts


def build_scene_segments(scene_cuts, fps, max_scene_duration=3.0):
    scene_segments = []
    max_scene_frames = int(max_scene_duration * fps)

    for i in range(len(scene_cuts) - 1):
        start = scene_cuts[i]
        end = scene_cuts[i + 1]

        if end > start:
            if (end - start) > max_scene_frames:
                end = start + max_scene_frames

            scene_segments.append((start, end))

    return scene_segments