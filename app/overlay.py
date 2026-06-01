"""On-frame UI: reps, stage, form score, and feedback messages."""

import cv2

from app.exercises.base import (
    SEVERITY_ERROR,
    SEVERITY_GOOD,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    ExerciseResult,
)

FONT = cv2.FONT_HERSHEY_SIMPLEX

SEVERITY_COLORS = {
    SEVERITY_GOOD: (0, 200, 0),
    SEVERITY_INFO: (0, 200, 200),
    SEVERITY_WARNING: (0, 165, 255),
    SEVERITY_ERROR: (0, 0, 255),
}


def _grade_color(score: float) -> tuple[int, int, int]:
    if score >= 90:
        return (0, 220, 0)
    if score >= 80:
        return (0, 220, 220)
    if score >= 70:
        return (0, 165, 255)
    if score >= 60:
        return (0, 110, 255)
    return (0, 0, 255)


def _panel(frame, x1, y1, x2, y2, alpha=0.55):
    """Draw a semi-transparent dark panel for readable text."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 0), -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


def draw_hud(frame, exercise_display: str, result: ExerciseResult, is_duration: bool):
    h, w = frame.shape[:2]

    # ---- top-left: exercise + reps/time + stage ----
    _panel(frame, 10, 10, 330, 135)
    cv2.putText(frame, exercise_display, (24, 42), FONT, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    if is_duration:
        cv2.putText(frame, f"Hold: {result.duration:4.1f}s", (24, 80), FONT, 0.8,
                    (255, 255, 255), 2, cv2.LINE_AA)
    else:
        cv2.putText(frame, f"Reps: {result.rep_count}", (24, 80), FONT, 0.8,
                    (255, 255, 255), 2, cv2.LINE_AA)

    cv2.putText(frame, f"Stage: {result.stage}", (24, 115), FONT, 0.6,
                (200, 200, 200), 1, cv2.LINE_AA)

    # ---- top-right: form score ----
    box_x1, box_y1 = w - 200, 10
    _panel(frame, box_x1, box_y1, w - 10, 130)
    color = _grade_color(result.form_score)
    cv2.putText(frame, "FORM", (box_x1 + 16, box_y1 + 28), FONT, 0.6, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(frame, f"{result.form_score:.0f}", (box_x1 + 16, box_y1 + 78), FONT, 1.4, color, 3, cv2.LINE_AA)
    cv2.putText(frame, result.grade, (box_x1 + 120, box_y1 + 78), FONT, 1.2, color, 2, cv2.LINE_AA)
    cv2.putText(frame, f"Avg: {result.avg_form_score:.0f}", (box_x1 + 16, box_y1 + 108), FONT, 0.5,
                (200, 200, 200), 1, cv2.LINE_AA)
    # progress bar
    bar_x, bar_y, bar_w = box_x1 + 16, box_y1 + 114, 170
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + 6), (90, 90, 90), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_w * result.form_score / 100), bar_y + 6), color, -1)

    # ---- bottom: feedback messages ----
    y = h - 24
    for fb in result.feedback[:3]:
        c = SEVERITY_COLORS.get(fb.severity, (255, 255, 255))
        (tw, th), _ = cv2.getTextSize(fb.message, FONT, 0.7, 2)
        _panel(frame, 16, y - th - 10, 16 + tw + 20, y + 8, alpha=0.5)
        cv2.putText(frame, fb.message, (26, y), FONT, 0.7, c, 2, cv2.LINE_AA)
        y -= th + 24

    # ---- help line ----
    cv2.putText(frame, "q/Esc quit  r reset  1 squat  2 deadlift  3 plank",
                (16, h - 4), FONT, 0.45, (180, 180, 180), 1, cv2.LINE_AA)


def draw_no_pose(frame, message: str = "No pose detected"):
    h, w = frame.shape[:2]
    cv2.putText(frame, message, (24, 42), FONT, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
