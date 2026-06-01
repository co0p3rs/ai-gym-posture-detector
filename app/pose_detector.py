"""MediaPipe Pose Landmarker (Tasks API) setup, detection, and drawing."""

from pathlib import Path
import urllib.request

import cv2
import mediapipe as mp
from mediapipe import Image, ImageFormat
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode
from mediapipe.tasks.python.vision import drawing_utils, PoseLandmarksConnections

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
MODEL_PATH = Path(__file__).resolve().parent.parent / "assets" / "pose_landmarker_lite.task"


def ensure_pose_model() -> str:
    """Download the lite pose model on first run if it is missing."""
    if MODEL_PATH.exists():
        return str(MODEL_PATH)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading pose model to {MODEL_PATH} ...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    return str(MODEL_PATH)


def create_pose_detector() -> PoseLandmarker:
    options = PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=ensure_pose_model()),
        running_mode=RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return PoseLandmarker.create_from_options(options)


def process_frame(landmarker: PoseLandmarker, frame_bgr, timestamp_ms: int):
    """Run pose estimation on a BGR frame."""
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    mp_image = Image(image_format=ImageFormat.SRGB, data=frame_rgb)
    return landmarker.detect_for_video(mp_image, timestamp_ms)


def get_pose_landmarks(results):
    """Return the first detected pose landmark list, or None."""
    if not results.pose_landmarks:
        return None
    return results.pose_landmarks[0]


def get_named_landmarks(results):
    """Return a name -> Landmark dict for the first detected pose, or None."""
    from app.landmarks import to_named_landmarks

    landmarks = get_pose_landmarks(results)
    if landmarks is None:
        return None
    return to_named_landmarks(landmarks)


def draw_pose(frame_bgr, results):
    """Draw pose landmarks and connections on the frame."""
    landmarks = get_pose_landmarks(results)
    if landmarks is None:
        return frame_bgr

    drawing_utils.draw_landmarks(
        frame_bgr,
        landmarks,
        PoseLandmarksConnections.POSE_LANDMARKS,
    )
    return frame_bgr
