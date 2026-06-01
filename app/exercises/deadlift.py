"""Deadlift rep counting and form checks."""

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


class Deadlift(RepCountingExercise):
    name = "deadlift"
    display_name = "Deadlift"

    # Primary angle = hip angle (shoulder-hip-knee).
    down_angle = 120.0   # hinged over the bar
    up_angle = 165.0     # standing lockout

    MIN_HINGE_BACK = 20.0   # below this at the bottom = barely hinging
    LOCKOUT_BACK_LEAN = 25.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._side = "left"

    def resolve_required(self, lm: dict[str, Landmark]) -> list[str]:
        self._side = best_side(lm, JOINTS)
        return [f"{self._side}_{j}" for j in JOINTS]

    def measure(self, lm: dict[str, Landmark]) -> dict[str, float]:
        s = self._side
        hip = calculate_angle(lm[f"{s}_shoulder"].xy, lm[f"{s}_hip"].xy, lm[f"{s}_knee"].xy)
        knee = calculate_angle(lm[f"{s}_hip"].xy, lm[f"{s}_knee"].xy, lm[f"{s}_ankle"].xy)
        back = angle_with_vertical(lm[f"{s}_shoulder"].xy, lm[f"{s}_hip"].xy)
        return {
            "primary": self.smooth("hip", hip),
            "hip": hip,
            "knee": knee,
            "back_lean": back,
        }

    def check_form(self, angles: dict[str, float], lm: dict[str, Landmark]) -> list[FormCheck]:
        checks: list[FormCheck] = []
        hip = angles["primary"]

        # At lockout the torso should be upright.
        if hip >= self.up_angle and angles["back_lean"] > self.LOCKOUT_BACK_LEAN:
            checks.append(FormCheck(
                20.0,
                Feedback("Stand tall, squeeze glutes", SEVERITY_INFO),
            ))

        # Encourage a proper hinge rather than a shallow tug.
        if self.stage == "down" and angles["back_lean"] < self.MIN_HINGE_BACK:
            checks.append(FormCheck(
                10.0,
                Feedback("Hinge at the hips", SEVERITY_INFO),
            ))

        # Very rounded-forward torso under load.
        if self.stage == "down" and angles["back_lean"] > 65:
            checks.append(FormCheck(
                25.0,
                Feedback("Keep your back flat", SEVERITY_WARNING),
            ))

        return checks
