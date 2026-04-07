from pathlib import Path
from moviepy import VideoFileClip, concatenate_videoclips


# Génère une vidéo "best-of" à partir des segments sélectionnés
def export_best_of(video_path, moments, output_name="best_of.mp4"):
    # Définition du chemin de sortie
    base_path = Path(__file__).resolve().parent.parent
    output_path = base_path / "outputs" / output_name

    print("🎬 Génération du best-of avec audio...")

    # Chargement de la vidéo source
    video = VideoFileClip(video_path)
    clips = []

    # Extraction des sous-clips correspondant aux moments sélectionnés
    for start, end in moments:
        start_sec = start / video.fps
        end_sec = end / video.fps

        # Vérifie la validité du segment
        if end_sec > start_sec:
            clip = video.subclipped(start_sec, end_sec)
            clips.append(clip)

    # Gestion du cas où aucun segment valide n'est disponible
    if not clips:
        print("⚠️ Aucun segment à exporter pour le best-of")
        video.close()
        return

    # Concaténation des clips pour former la vidéo finale
    final_clip = concatenate_videoclips(clips)

    # Export du fichier vidéo avec codecs standards (vidéo + audio)
    final_clip.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac"
    )

    # Libération des ressources
    final_clip.close()
    video.close()

    print(f"✅ Best-of exporté : {output_path}")