import pytest

from app.exercises import available_exercises, create_exercise
from app.exercises.base import best_side, score_to_grade
from app.landmarks import LANDMARK_MAP, Landmark


class Clock:
    """Deterministic stand-in for time.monotonic in tests."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def tick(self, dt=1.0):
        self.t += dt


def make_lm(coords, visibility=1.0):
    """Build a full named-landmark dict; unspecified joints are invisible."""
    lm = {}
    for name in LANDMARK_MAP:
        if name in coords:
            x, y = coords[name]
            lm[name] = Landmark(x, y, visibility)
        else:
            lm[name] = Landmark(0.0, 0.0, 0.0)
    return lm


# ---- coordinate fixtures (left side, side view) ----
SQUAT_STAND = make_lm({
    "left_shoulder": (0.5, 0.20),
    "left_hip": (0.5, 0.50),
    "left_knee": (0.5, 0.70),
    "left_ankle": (0.5, 0.90),
})
SQUAT_DEEP = make_lm({
    "left_shoulder": (0.5, 0.45),
    "left_hip": (0.5, 0.55),
    "left_knee": (0.6, 0.60),
    "left_ankle": (0.5, 0.70),
})


def feed(exercise, lm, frames):
    result = None
    for _ in range(frames):
        result = exercise.update(lm)
    return result


def test_registry_lists_three_exercises():
    assert set(available_exercises()) == {"squat", "deadlift", "plank"}


def test_create_unknown_exercise_raises():
    with pytest.raises(ValueError):
        create_exercise("backflip")


def test_best_side_prefers_more_visible():
    lm = make_lm({"left_hip": (0.5, 0.5)}, visibility=1.0)
    # right side joints are invisible (vis 0)
    assert best_side(lm, ["hip", "knee"]) == "left"


def test_score_to_grade_boundaries():
    assert score_to_grade(95) == "A"
    assert score_to_grade(85) == "B"
    assert score_to_grade(72) == "C"
    assert score_to_grade(61) == "D"
    assert score_to_grade(40) == "F"


def test_squat_counts_one_clean_rep():
    sq = create_exercise("squat")
    clock = Clock()
    sq._clock = clock

    feed(sq, SQUAT_STAND, 6)
    clock.tick()
    feed(sq, SQUAT_DEEP, 6)
    clock.tick()
    result = feed(sq, SQUAT_STAND, 6)

    assert result.rep_count == 1
    assert result.stage == "up"


def test_squat_partial_rep_not_counted():
    sq = create_exercise("squat")
    clock = Clock()
    sq._clock = clock

    feed(sq, SQUAT_STAND, 6)
    clock.tick()
    # only a half-depth dip that never crosses the down threshold
    half = make_lm({
        "left_shoulder": (0.5, 0.30),
        "left_hip": (0.5, 0.50),
        "left_knee": (0.5, 0.68),
        "left_ankle": (0.5, 0.90),
    })
    feed(sq, half, 6)
    clock.tick()
    result = feed(sq, SQUAT_STAND, 6)

    assert result.rep_count == 0


def test_squat_reset_clears_state():
    sq = create_exercise("squat")
    sq._clock = Clock()
    feed(sq, SQUAT_STAND, 3)
    feed(sq, SQUAT_DEEP, 6)
    feed(sq, SQUAT_STAND, 6)
    sq.reset()
    assert sq.rep_count == 0
    assert sq.stage == "up"


def test_squat_invalid_pose_when_landmarks_hidden():
    sq = create_exercise("squat")
    result = sq.update(make_lm({}))  # nothing visible
    assert result.is_valid_pose is False
    assert result.form_score == 0.0


def test_squat_clean_depth_scores_well():
    sq = create_exercise("squat")
    sq._clock = Clock()
    result = feed(sq, SQUAT_DEEP, 6)
    assert result.form_score >= 80
    assert result.grade in {"A", "B"}


def test_deadlift_counts_one_rep():
    dl = create_exercise("deadlift")
    clock = Clock()
    dl._clock = clock

    lockout = make_lm({
        "left_shoulder": (0.5, 0.20),
        "left_hip": (0.5, 0.50),
        "left_knee": (0.5, 0.72),
        "left_ankle": (0.5, 0.90),
    })
    hinge = make_lm({
        "left_shoulder": (0.78, 0.42),
        "left_hip": (0.5, 0.50),
        "left_knee": (0.5, 0.72),
        "left_ankle": (0.5, 0.90),
    })

    feed(dl, lockout, 6)
    clock.tick()
    feed(dl, hinge, 6)
    clock.tick()
    result = feed(dl, lockout, 6)

    assert result.rep_count == 1


def test_plank_accumulates_hold_time():
    plank = create_exercise("plank")
    clock = Clock()
    plank._clock = clock

    hold = make_lm({
        "left_shoulder": (0.20, 0.50),
        "left_hip": (0.50, 0.52),
        "left_ankle": (0.80, 0.54),
    })

    plank.update(hold)          # t=0 -> hold starts
    clock.tick(3.0)
    result = plank.update(hold)  # t=3 -> 3s held

    assert result.stage == "hold"
    assert result.duration == pytest.approx(3.0, abs=1e-6)


def test_plank_detects_hip_sag():
    plank = create_exercise("plank")
    plank._clock = Clock()

    sag = make_lm({
        "left_shoulder": (0.20, 0.50),
        "left_hip": (0.50, 0.64),
        "left_ankle": (0.80, 0.54),
    })
    result = plank.update(sag)
    messages = " ".join(fb.message.lower() for fb in result.feedback)
    assert "sag" in messages or "hips" in messages
    assert result.stage != "hold"
