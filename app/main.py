"""Video loop: pose detection, exercise analysis, and on-screen feedback.

Input is either a webcam (default) or a video file (e.g. a clip filmed on a
phone at the gym). Switch exercises live with number keys.
"""

import time

import cv2

from app.exercises import create_exercise
from app.exercises.base import DurationExercise
from app.overlay import draw_hud, draw_no_pose
from app.pose_detector import create_pose_detector, draw_pose, get_named_landmarks, process_frame

WINDOW_NAME = "AI Gym Posture Detector"

EXERCISE_KEYS = {
    ord("1"): "squat",
    ord("2"): "deadlift",
    ord("3"): "plank",
}


def _open_capture(video: str | None, camera_index: int):
    if video:
        cap = cv2.VideoCapture(video)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {video}")
        return cap, False
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open webcam (index {camera_index}). "
            "Check the camera is connected and not used by another app."
        )
    return cap, True


def main(exercise_name: str = "squat", video: str | None = None, camera_index: int = 0):
    cap, is_webcam = _open_capture(video, camera_index)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    landmarker = create_pose_detector()
    exercise = create_exercise(exercise_name)

    frame_index = 0
    last_ts = -1
    start = time.monotonic()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                if is_webcam:
                    break
                # video finished: hold the last frame until the user quits
                if cv2.waitKey(0) & 0xFF == ord("q"):
                    break
                continue

            if is_webcam:
                frame = cv2.flip(frame, 1)
                timestamp_ms = int((time.monotonic() - start) * 1000)
            else:
                timestamp_ms = int(frame_index * 1000 / fps)
            timestamp_ms = max(timestamp_ms, last_ts + 1)
            last_ts = timestamp_ms
            frame_index += 1

            results = process_frame(landmarker, frame, timestamp_ms)
            frame = draw_pose(frame, results)
            named = get_named_landmarks(results)

            if named is None:
                draw_no_pose(frame)
            else:
                result = exercise.update(named)
                draw_hud(
                    frame,
                    exercise.display_name,
                    result,
                    is_duration=isinstance(exercise, DurationExercise),
                )

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("r"):
                exercise.reset()
            elif key in EXERCISE_KEYS:
                new_name = EXERCISE_KEYS[key]
                if new_name != exercise.name:
                    exercise = create_exercise(new_name)
    finally:
        cap.release()
        landmarker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
