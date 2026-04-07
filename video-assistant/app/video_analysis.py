import cv2
import numpy as np
from app.utils import normalize_signal

# Calcule un score de mouvement pour chaque frame de la vidéo
def compute_motion_scores(video_path):
    cap = cv2.VideoCapture(video_path)

    # Vérifie que la vidéo peut bien être ouverte
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la vidéo")
        return None, None, None
    
    # Récupération des métadonnées principales de la vidéo
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print("📊 Analyse en cours...")
    print(f"Frames totales : {frame_count}")
    print(f"FPS : {fps}")
    # Lecture de la première frame, utilisée comme référence initiale
    ret, prev_frame = cap.read()
    if not ret:
        print("❌ Impossible de lire la première frame")
        cap.release()
        return None, None, None
    
    # Conversion en niveaux de gris pour simplifier l'analyse
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    # Calcul de l'histogramme initial pour comparer les variations visuelles globales
    prev_hist = cv2.calcHist([prev_gray], [0], None, [256], [0, 256])
    prev_hist = cv2.normalize(prev_hist, prev_hist).flatten()

    frame_index = 1
    motion_scores = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Affichage périodique de la progression
        if frame_index % 100 == 0:
            progress = frame_index / frame_count * 100
            print(f"Progression : {progress:.1f}%")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Histogramme de la frame courante
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()

        # Différence pixel à pixel entre deux frames successives
        diff = cv2.absdiff(prev_gray, gray)
        motion_score = np.mean(diff)

        # Différence entre histogrammes pour détecter les changements visuels globaux
        hist_diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
        # Score fusionné : mouvement local + variation globale d'apparence
        combined_score = motion_score + hist_diff * 50
        motion_scores.append(combined_score)
        # Mise à jour des références pour l'itération suivante
        prev_hist = hist
        prev_gray = gray
        frame_index += 1

    cap.release()

    # Conversion en tableau NumPy pour faciliter les traitements ultérieurs
    motion_array = np.array(motion_scores)
    return motion_array, fps, frame_count

# Détecte les coupures de scène à partir des pics du signal de mouvement
def detect_scene_cuts(motion_array, fps, k_video_cut=2.0):
    # Normalisation du signal pour rendre le seuil plus robuste
    motion_norm = normalize_signal(motion_array)

    # Calcul d'un seuil dynamique basé sur la moyenne et l'écart-type
    mean_motion = np.mean(motion_norm)
    std_motion = np.std(motion_norm)
    threshold = mean_motion + k_video_cut * std_motion
    raw_cuts = np.where(motion_norm > threshold)[0]

    scene_cuts = []
    min_gap = int(fps * 0.5) # écart minimal entre deux coupures
    last_cut = -min_gap

    # Filtre les coupures trop proches pour éviter les doublons
    for cut in raw_cuts:
        if cut - last_cut >= min_gap:
            scene_cuts.append(cut)
            last_cut = cut

    return mean_motion, std_motion, threshold, scene_cuts

# Construit des segments de scène exploitables à partir des coupures détectées
def build_scene_segments(scene_cuts, fps, max_scene_duration=3.0):
    scene_segments = []
    max_scene_frames = int(max_scene_duration * fps)

    # Chaque segment est défini entre deux coupures successives
    for i in range(len(scene_cuts) - 1):
        start = scene_cuts[i]
        end = scene_cuts[i + 1]

        if end > start:
            # Limite la durée maximale d'une scène pour garder un montage dynamique
            if (end - start) > max_scene_frames:
                end = start + max_scene_frames

            scene_segments.append((start, end))

    return scene_segments