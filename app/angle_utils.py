"""Pure geometry helpers for joint angles.

All functions take 2D points as (x, y). Coordinates can be normalized
(0..1) or pixels; angles are scale-invariant either way.
"""

import numpy as np

Point = tuple[float, float]


def calculate_angle(point_a: Point, point_b: Point, point_c: Point) -> float:
    """Inner angle at point_b (degrees) for the triangle a-b-c."""
    a = np.array(point_a, dtype=float)
    b = np.array(point_b, dtype=float)
    c = np.array(point_c, dtype=float)

    ba = a - b
    bc = c - b
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-8 or norm_bc < 1e-8:
        return 0.0

    cosine = np.dot(ba, bc) / (norm_ba * norm_bc)
    cosine = np.clip(cosine, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def angle_with_vertical(top: Point, bottom: Point) -> float:
    """
    Angle (degrees) of the segment bottom->top relative to the vertical axis.

    0 means perfectly upright. Useful for torso lean checks.
    Note: image y grows downward, so "up" is the -y direction.
    """
    vector = np.array([top[0] - bottom[0], top[1] - bottom[1]], dtype=float)
    norm = np.linalg.norm(vector)
    if norm < 1e-8:
        return 0.0
    vertical = np.array([0.0, -1.0])
    cosine = np.clip(np.dot(vector, vertical) / norm, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def angle_with_horizontal(point_a: Point, point_b: Point) -> float:
    """
    Absolute angle (degrees, 0..90) of segment a-b relative to horizontal.

    0 means perfectly flat. Useful for plank body-line checks.
    """
    dx = point_b[0] - point_a[0]
    dy = point_b[1] - point_a[1]
    if abs(dx) < 1e-8 and abs(dy) < 1e-8:
        return 0.0
    return float(abs(np.degrees(np.arctan2(abs(dy), abs(dx)))))
