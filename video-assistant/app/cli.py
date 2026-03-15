from pathlib import Path
from app.analyze_video import analyze_video

def main():
    video_path = Path("data/test.mp4")
    analyze_video(str(video_path))

if __name__ == "__main__":
    main()