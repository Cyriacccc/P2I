from pathlib import Path
from moviepy import VideoFileClip, concatenate_videoclips


def export_best_of(video_path, moments, output_name="best_of.mp4"):
    base_path = Path(__file__).resolve().parent.parent
    output_path = base_path / "outputs" / output_name

    print("🎬 Génération du best-of avec audio...")

    video = VideoFileClip(video_path)
    clips = []

    for start, end in moments:
        start_sec = start / video.fps
        end_sec = end / video.fps

        if end_sec > start_sec:
            clip = video.subclipped(start_sec, end_sec)
            clips.append(clip)

    if not clips:
        print("⚠️ Aucun segment à exporter pour le best-of")
        video.close()
        return

    final_clip = concatenate_videoclips(clips)

    final_clip.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac"
    )

    final_clip.close()
    video.close()

    print(f"✅ Best-of exporté : {output_path}")