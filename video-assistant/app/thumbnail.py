from pathlib import Path
import cv2
import numpy as np


def generate_thumbnail(video_path, moment, motion_array):
    start, end, score = moment

    best_frame = start + np.argmax(motion_array[start:end])

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(best_frame))

    ret, frame = cap.read()

    if ret:
        base_path = Path(__file__).resolve().parent.parent
        output_path = base_path / "outputs" / "thumbnail.png"
        cv2.imwrite(str(output_path), frame)
        print("🖼️ Miniature générée :", output_path)

    cap.release()