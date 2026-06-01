"""Base exercise engine: rep counting (FSM), form scoring, and feedback.

Design notes:
- Exercise logic lives in small Python subclasses (no eval of config strings),
  which keeps it safe and easy to unit-test.
- Subclasses describe their angles and form rules; the base handles the
  finite-state machine, repetition counting, smoothing, and form score.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from app.landmarks import Landmark, missing_landmarks


SEVERITY_GOOD = "good"
SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"


@dataclass
class Feedback:
    message: str
    severity: str = SEVERITY_INFO


@dataclass
class FormCheck:
    """A single form-rule outcome: how many points to deduct + the message."""

    penalty: float
    feedback: Feedback


@dataclass
class ExerciseResult:
    rep_count: int
    stage: str
    feedback: list[Feedback]
    form_score: float
    grade: str
    avg_form_score: float
    angles: dict[str, float] = field(default_factory=dict)
    is_valid_pose: bool = True
    duration: float = 0.0


def best_side(lm: dict[str, Landmark], joints: list[str]) -> str:
    """Pick the body side ('left'/'right') with the higher total visibility."""
    def score(side: str) -> float:
        return sum(lm[f"{side}_{j}"].visibility for j in joints if f"{side}_{j}" in lm)

    return "left" if score("left") >= score("right") else "right"


def score_to_grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


class BaseExercise:
    """Shared state and helpers for all exercises."""

    name = "base"
    display_name = "Base"
    required_landmarks: list[str] = []

    def __init__(
        self,
        smoothing_window: int = 5,
        visibility_threshold: float = 0.5,
    ):
        self.smoothing_window = smoothing_window
        self.visibility_threshold = visibility_threshold
        self._angle_history: dict[str, deque] = {}
        self.rep_count = 0
        self.stage = "ready"
        self.rep_scores: list[float] = []
        self.current_form_score = 100.0
        self.avg_form_score = 100.0

    # ---- to be implemented by subclasses ----
    def measure(self, lm: dict[str, Landmark]) -> dict[str, float]:
        """Return all angles needed; must include a 'primary' key."""
        raise NotImplementedError

    def check_form(self, angles: dict[str, float], lm: dict[str, Landmark]) -> list[FormCheck]:
        """Return form-rule outcomes for the current frame."""
        return []

    def _update_state(self, angles: dict[str, float]) -> None:
        """Advance the FSM / rep counter. Implemented by subclasses."""
        raise NotImplementedError

    def resolve_required(self, lm: dict[str, Landmark]) -> list[str]:
        """Landmarks that must be visible this frame (override for sided moves)."""
        return self.required_landmarks

    # ---- shared machinery ----
    def reset(self) -> None:
        self.rep_count = 0
        self.stage = "ready"
        self.rep_scores.clear()
        self.current_form_score = 100.0
        self.avg_form_score = 100.0
        self._angle_history.clear()

    def smooth(self, key: str, value: float) -> float:
        history = self._angle_history.setdefault(key, deque(maxlen=self.smoothing_window))
        history.append(value)
        return sum(history) / len(history)

    def update(self, lm: dict[str, Landmark]) -> ExerciseResult:
        required = self.resolve_required(lm)
        missing = missing_landmarks(lm, required, self.visibility_threshold)
        if missing:
            pretty = ", ".join(m.replace("_", " ") for m in missing)
            return ExerciseResult(
                rep_count=self.rep_count,
                stage=self.stage,
                feedback=[Feedback(f"Can't see: {pretty}", SEVERITY_ERROR)],
                form_score=0.0,
                grade="-",
                avg_form_score=self.avg_form_score,
                is_valid_pose=False,
            )

        angles = self.measure(lm)
        checks = self.check_form(angles, lm)

        penalty = sum(c.penalty for c in checks)
        self.current_form_score = max(0.0, 100.0 - penalty)

        self._update_state(angles)

        feedback = [c.feedback for c in checks]
        if not feedback:
            feedback = [Feedback("Good form", SEVERITY_GOOD)]

        return ExerciseResult(
            rep_count=self.rep_count,
            stage=self.stage,
            feedback=feedback,
            form_score=self.current_form_score,
            grade=score_to_grade(self.current_form_score),
            avg_form_score=self.avg_form_score,
            angles=angles,
            is_valid_pose=True,
        )

    def _record_rep_score(self, score: float) -> None:
        self.rep_scores.append(score)
        self.avg_form_score = sum(self.rep_scores) / len(self.rep_scores)


class RepCountingExercise(BaseExercise):
    """
    Angle-driven rep counter.

    A rep is counted when the primary angle drops below `down_angle`
    (bottom reached) and then rises back above `up_angle` (lockout).
    """

    down_angle = 90.0
    up_angle = 160.0

    def __init__(self, min_rep_seconds: float = 0.5, **kwargs):
        super().__init__(**kwargs)
        self.min_rep_seconds = min_rep_seconds
        self.stage = "up"
        self._reached_bottom = False
        self._last_count_time = 0.0
        self._rep_min_score = 100.0
        self._clock = time.monotonic

    def reset(self) -> None:
        super().reset()
        self.stage = "up"
        self._reached_bottom = False
        self._last_count_time = 0.0
        self._rep_min_score = 100.0

    def _update_state(self, angles: dict[str, float]) -> None:
        angle = angles["primary"]

        # Track worst form during the descent/bottom of the current rep.
        if self.stage != "up":
            self._rep_min_score = min(self._rep_min_score, self.current_form_score)

        if angle <= self.down_angle:
            self.stage = "down"
            self._reached_bottom = True
            self._rep_min_score = min(self._rep_min_score, self.current_form_score)
        elif angle >= self.up_angle:
            if self.stage == "down" and self._reached_bottom:
                now = self._clock()
                if now - self._last_count_time >= self.min_rep_seconds:
                    self.rep_count += 1
                    self._last_count_time = now
                    self._record_rep_score(self._rep_min_score)
                self._reached_bottom = False
                self._rep_min_score = 100.0
            self.stage = "up"
        else:
            if self.stage == "up":
                self.stage = "descending"


class DurationExercise(BaseExercise):
    """Holds-based exercise (e.g. plank): accumulates time while in position."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stage = "ready"
        self.hold_duration = 0.0
        self._hold_start: float | None = None
        self._clock = time.monotonic

    def reset(self) -> None:
        super().reset()
        self.stage = "ready"
        self.hold_duration = 0.0
        self._hold_start = None

    def _update_state(self, angles: dict[str, float]) -> None:
        # Duration exercises drive state from hold time, handled in update().
        pass

    def is_holding(self, angles: dict[str, float], lm: dict[str, Landmark]) -> bool:
        raise NotImplementedError

    def update(self, lm: dict[str, Landmark]) -> ExerciseResult:
        result = super().update(lm)
        if not result.is_valid_pose:
            self._hold_start = None
            self.stage = "broken"
            result.duration = self.hold_duration
            return result

        angles = result.angles
        holding = self.is_holding(angles, lm)
        now = self._clock()

        if holding:
            if self._hold_start is None:
                self._hold_start = now
            self.hold_duration = now - self._hold_start
            self.stage = "hold"
        else:
            self._hold_start = None
            self.stage = "rest"

        result.stage = self.stage
        result.duration = self.hold_duration
        return result
