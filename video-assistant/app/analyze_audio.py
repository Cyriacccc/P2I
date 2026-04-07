import numpy as np
from moviepy import VideoFileClip


# Calcule un score audio (énergie) par frame vidéo
def compute_audio_scores(video_path, fps):
    video = VideoFileClip(video_path)

    # Vérifie la présence d'une piste audio
    if video.audio is None:
        print("⚠️ Pas de piste audio détectée")
        video.close()
        return np.array([])

    # Extraction du signal audio (échantillonné à 22050 Hz)
    audio = video.audio.to_soundarray(fps=22050)

    # Conversion en mono si audio stéréo (moyenne des canaux)
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)

    # Nombre d'échantillons audio correspondant à une frame vidéo
    samples_per_frame = int(22050 / fps)
    audio_scores = []

    # Découpage du signal audio en segments synchronisés avec les frames vidéo
    for i in range(0, len(audio), samples_per_frame):
        chunk = audio[i:i + samples_per_frame]

        if len(chunk) > 0:
            # Calcul de l'énergie moyenne (intensité sonore)
            energy = np.mean(np.abs(chunk))
            audio_scores.append(energy)

    video.close()

    # Retourne un tableau contenant un score audio par frame
    return np.array(audio_scores)