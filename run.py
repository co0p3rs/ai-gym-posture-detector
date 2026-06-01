import argparse

from app.exercises import available_exercises
from app.main import main


def parse_args():
    parser = argparse.ArgumentParser(description="AI Gym Posture Detector")
    parser.add_argument(
        "--exercise", "-e", default="squat", choices=available_exercises(),
        help="Exercise to analyze (default: squat)",
    )
    parser.add_argument(
        "--video", "-v", default=None,
        help="Path to a video file. Omit to use the webcam.",
    )
    parser.add_argument(
        "--camera", "-c", type=int, default=0,
        help="Webcam index (default: 0)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(exercise_name=args.exercise, video=args.video, camera_index=args.camera)
