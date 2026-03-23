from pathlib import Path
from app.analyze_video import analyze_video


def main():
    video_path = Path("data/samples/test.mp4")

    audio_sensitivity = input(
        "Choisissez la sensibilité audio (sensible / equilibree / stricte) : "
    ).strip().lower()

    if audio_sensitivity == "sensible":
        k_audio = 0.4
    elif audio_sensitivity == "stricte":
        k_audio = 1.2
    else:
        k_audio = 0.7

    video_sensitivity = input(
        "Choisissez la sensibilité vidéo (sensible / equilibree / stricte) : "
    ).strip().lower()

    if video_sensitivity == "sensible":
        k_video_cut = 1.5
        k_video_highlight = 0.5
    elif video_sensitivity == "stricte":
        k_video_cut = 2.5
        k_video_highlight = 1.0
    else:
        k_video_cut = 2.0
        k_video_highlight = 0.7

    print(f"Sensibilité audio choisie : {audio_sensitivity} | k_audio = {k_audio}")
    print(
        f"Sensibilité vidéo choisie : {video_sensitivity} | "
        f"k_video_cut = {k_video_cut}, k_video_highlight = {k_video_highlight}"
    )

    analyze_video(
        str(video_path),
        k_audio=k_audio,
        k_video_cut=k_video_cut,
        k_video_highlight=k_video_highlight
    )


if __name__ == "__main__":
    main()