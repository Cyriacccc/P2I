from pathlib import Path
from moviepy import VideoFileClip, concatenate_videoclips


def export_best_of(video_path, moments, output_name="best_of.mp4"):
    """
    Génère un Best Of à partir des segments sélectionnés.

    output_name permet à l'application web d'attribuer un nom
    unique à chaque vidéo générée.
    """
    base_path = Path(__file__).resolve().parent.parent
    output_dir = base_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / output_name

    print("🎬 Génération du Best Of avec audio...")

    video = VideoFileClip(str(video_path))
    clips = []
    final_clip = None

    try:
        for start, end in moments:
            start_sec = start / video.fps
            end_sec = end / video.fps

            # Limite les segments à la durée réelle de la vidéo.
            start_sec = max(0, start_sec)
            end_sec = min(video.duration, end_sec)

            if end_sec > start_sec:
                clips.append(video.subclipped(start_sec, end_sec))

        if not clips:
            raise ValueError("Aucun segment valide à exporter.")

        final_clip = concatenate_videoclips(clips)

        final_clip.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

    finally:
        if final_clip is not None:
            final_clip.close()

        for clip in clips:
            clip.close()

        video.close()

    print(f"✅ Best Of exporté : {output_path}")
    return output_path
