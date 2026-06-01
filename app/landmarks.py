"""Named access to MediaPipe Pose landmarks."""

from dataclasses import dataclass

# MediaPipe Pose landmark indices
LANDMARK_MAP = {
    "nose": 0,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
}


@dataclass(frozen=True)
class Landmark:
    """A single pose point in normalized coordinates (0..1)."""

    x: float
    y: float
    visibility: float

    @property
    def xy(self) -> tuple[float, float]:
        return (self.x, self.y)


def to_named_landmarks(mp_landmarks) -> dict[str, Landmark]:
    """Convert a MediaPipe landmark list into a name -> Landmark dict."""
    named: dict[str, Landmark] = {}
    for name, idx in LANDMARK_MAP.items():
        lm = mp_landmarks[idx]
        visibility = getattr(lm, "visibility", 1.0)
        named[name] = Landmark(x=lm.x, y=lm.y, visibility=visibility)
    return named


def all_visible(landmarks: dict[str, Landmark], names, threshold: float = 0.5) -> bool:
    """True if every requested landmark is present and visible enough."""
    for name in names:
        lm = landmarks.get(name)
        if lm is None or lm.visibility < threshold:
            return False
    return True


def missing_landmarks(landmarks: dict[str, Landmark], names, threshold: float = 0.5) -> list[str]:
    """Return the names that are absent or below the visibility threshold."""
    missing = []
    for name in names:
        lm = landmarks.get(name)
        if lm is None or lm.visibility < threshold:
            missing.append(name)
    return missing
