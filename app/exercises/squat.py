"""Squat: knee-angle rep counting + depth, back, and knee-tracking feedback."""

from app.angle_utils import angle_with_vertical, calculate_angle
from app.exercises.base import (
    SEVERITY_INFO,
    SEVERITY_WARNING,
    Feedback,
    FormCheck,
    RepCountingExercise,
    best_side,
)
from app.landmarks import Landmark

JOINTS = ["shoulder", "hip", "knee", "ankle"]


class Squat(RepCountingExercise):
    name = "squat"
    display_name = "Squat"

    down_angle = 95.0
    up_angle = 160.0

    GOOD_DEPTH_ANGLE = 95.0
    SHALLOW_ANGLE = 140.0
    MAX_BACK_LEAN = 50.0
    KNEE_OVER_TOE = 0.07

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._side = "left"

    def resolve_required(self, lm: dict[str, Landmark]) -> list[str]:
        self._side = best_side(lm, JOINTS)
        return [f"{self._side}_{j}" for j in JOINTS]

    def measure(self, lm: dict[str, Landmark]) -> dict[str, float]:
        s = self._side
        knee = calculate_angle(lm[f"{s}_hip"].xy, lm[f"{s}_knee"].xy, lm[f"{s}_ankle"].xy)
        hip = calculate_angle(lm[f"{s}_shoulder"].xy, lm[f"{s}_hip"].xy, lm[f"{s}_knee"].xy)
        back = angle_with_vertical(lm[f"{s}_shoulder"].xy, lm[f"{s}_hip"].xy)
        return {
            "primary": self.smooth("knee", knee),
            "knee": knee,
            "hip": hip,
            "back_lean": back,
        }

    def check_form(self, angles: dict[str, float], lm: dict[str, Landmark]) -> list[FormCheck]:
        checks: list[FormCheck] = []
        knee = angles["primary"]

        if angles["back_lean"] > self.MAX_BACK_LEAN and knee < 140:
            over = angles["back_lean"] - self.MAX_BACK_LEAN
            checks.append(FormCheck(
                min(30.0, over * 1.5),
                Feedback("Keep your chest up", SEVERITY_WARNING),
            ))

        s = self._side
        knee_x = lm[f"{s}_knee"].x
        ankle_x = lm[f"{s}_ankle"].x
        overshoot = (ankle_x - knee_x) if s == "left" else (knee_x - ankle_x)
        if overshoot > self.KNEE_OVER_TOE and knee < 140:
            checks.append(FormCheck(
                min(25.0, overshoot * 200),
                Feedback("Knees going past toes", SEVERITY_WARNING),
            ))

        if self.stage == "down" and self.SHALLOW_ANGLE > knee > self.GOOD_DEPTH_ANGLE:
            checks.append(FormCheck(
                15.0,
                Feedback("Go lower", SEVERITY_INFO),
            ))

        return checks
