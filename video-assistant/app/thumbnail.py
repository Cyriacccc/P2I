from pathlib import Path
import cv2
import numpy as np

# Génère une miniature (thumbnail) représentative d'un moment fort de la vidéo
def generate_thumbnail(video_path, moment, motion_array, output_dir=None):
    start, end, score = moment

    # Sélection de la frame la plus "intense" (score maximal) dans le segment
    best_frame = start + np.argmax(motion_array[start:end])

    # Ouverture de la vidéo et positionnement sur la frame sélectionnée
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(best_frame))

    ret, frame = cap.read()

    if ret:
        # Construction du chemin de sortie (dossier outputs à la racine du projet)
        if output_dir is None:
           base_path = Path(__file__).resolve().parent.parent
           output_dir = base_path / "outputs"
        else:
           output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "thumbnail.png"
        # Sauvegarde de l'image extraite
        cv2.imwrite(str(output_path), frame)
        print("🖼️ Miniature générée :", output_path)
    # Libération des ressources vidéo
    cap.release()