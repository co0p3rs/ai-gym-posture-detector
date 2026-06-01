"""Plank: hold-duration exercise with hip-sag / hip-pike feedback."""

from app.angle_utils import angle_with_horizontal, calculate_angle
from app.exercises.base import (
    SEVERITY_INFO,
    SEVERITY_WARNING,
    Feedback,
    FormCheck,
    DurationExercise,
    best_side,
)
from app.landmarks import Landmark

JOINTS = ["shoulder", "hip", "ankle"]


class Plank(DurationExercise):
    name = "plank"
    display_name = "Plank"

    STRAIGHT_BODY_MIN = 160.0   # shoulder-hip-ankle near 180 = straight
    MAX_BODY_TILT = 35.0        # body line should be roughly horizontal
    SAG_ANGLE = 165.0           # below this = hips dropping or piking

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._side = "left"

    def resolve_required(self, lm: dict[str, Landmark]) -> list[str]:
        self._side = best_side(lm, JOINTS)
        return [f"{self._side}_{j}" for j in JOINTS]

    def measure(self, lm: dict[str, Landmark]) -> dict[str, float]:
        s = self._side
        body = calculate_angle(lm[f"{s}_shoulder"].xy, lm[f"{s}_hip"].xy, lm[f"{s}_ankle"].xy)
        tilt = angle_with_horizontal(lm[f"{s}_shoulder"].xy, lm[f"{s}_ankle"].xy)
        return {
            "primary": self.smooth("body", body),
            "body": body,
            "tilt": tilt,
        }

    def is_holding(self, angles: dict[str, float], lm: dict[str, Landmark]) -> bool:
        return angles["primary"] >= self.STRAIGHT_BODY_MIN and angles["tilt"] <= self.MAX_BODY_TILT

    def check_form(self, angles: dict[str, float], lm: dict[str, Landmark]) -> list[FormCheck]:
        checks: list[FormCheck] = []
        body = angles["primary"]
        s = self._side

        if angles["tilt"] > self.MAX_BODY_TILT:
            checks.append(FormCheck(
                10.0,
                Feedback("Get into plank position", SEVERITY_INFO),
            ))
            return checks

        if body < self.SAG_ANGLE:
            hip_y = lm[f"{s}_hip"].y
            shoulder_y = lm[f"{s}_shoulder"].y
            ankle_y = lm[f"{s}_ankle"].y
            line_mid_y = (shoulder_y + ankle_y) / 2
            if hip_y > line_mid_y:
                checks.append(FormCheck(25.0, Feedback("Hips sagging, lift them", SEVERITY_WARNING)))
            else:
                checks.append(FormCheck(20.0, Feedback("Hips too high, lower them", SEVERITY_WARNING)))

        return checks
