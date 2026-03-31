import numpy as np
from moviepy import VideoFileClip


def compute_audio_scores(video_path, fps):
    video = VideoFileClip(video_path)

    if video.audio is None:
        print("⚠️ Pas de piste audio détectée")
        video.close()
        return np.array([])

    audio = video.audio.to_soundarray(fps=22050)

    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)

    samples_per_frame = int(22050 / fps)
    audio_scores = []

    for i in range(0, len(audio), samples_per_frame):
        chunk = audio[i:i + samples_per_frame]

        if len(chunk) > 0:
            energy = np.mean(np.abs(chunk))
            audio_scores.append(energy)

    video.close()
    return np.array(audio_scores)