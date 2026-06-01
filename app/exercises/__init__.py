"""Exercise registry: look up exercises by name."""

from app.exercises.base import BaseExercise
from app.exercises.deadlift import Deadlift
from app.exercises.plank import Plank
from app.exercises.squat import Squat

_REGISTRY: dict[str, type[BaseExercise]] = {
    Squat.name: Squat,
    Deadlift.name: Deadlift,
    Plank.name: Plank,
}


def available_exercises() -> list[str]:
    return list(_REGISTRY)


def create_exercise(name: str) -> BaseExercise:
    key = name.lower().strip()
    if key not in _REGISTRY:
        raise ValueError(
            f"Unknown exercise '{name}'. Available: {', '.join(_REGISTRY)}"
        )
    return _REGISTRY[key]()
