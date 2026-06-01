import math

import pytest

from app.angle_utils import angle_with_horizontal, angle_with_vertical, calculate_angle


def test_calculate_angle_right_angle():
    assert calculate_angle((1, 0), (0, 0), (0, 1)) == pytest.approx(90.0, abs=1e-5)


def test_calculate_angle_straight_line():
    assert calculate_angle((0, 0), (1, 0), (2, 0)) == pytest.approx(180.0, abs=1e-5)


def test_calculate_angle_acute():
    assert calculate_angle((1, 0), (0, 0), (1, 1)) == pytest.approx(45.0, abs=1e-5)


def test_calculate_angle_zero_length_returns_zero():
    assert calculate_angle((0, 0), (0, 0), (1, 1)) == 0.0


def test_calculate_angle_equilateral_is_60():
    angle = calculate_angle((1, 0), (0, 0), (0.5, math.sqrt(3) / 2))
    assert angle == pytest.approx(60.0, abs=0.1)


def test_angle_with_vertical_upright_is_zero():
    # top directly above bottom (image y grows downward)
    assert angle_with_vertical((0.5, 0.2), (0.5, 0.8)) == pytest.approx(0.0, abs=1e-5)


def test_angle_with_vertical_horizontal_is_90():
    assert angle_with_vertical((0.8, 0.5), (0.2, 0.5)) == pytest.approx(90.0, abs=1e-5)


def test_angle_with_horizontal_flat_is_zero():
    assert angle_with_horizontal((0.2, 0.5), (0.8, 0.5)) == pytest.approx(0.0, abs=1e-5)


def test_angle_with_horizontal_vertical_is_90():
    assert angle_with_horizontal((0.5, 0.2), (0.5, 0.8)) == pytest.approx(90.0, abs=1e-5)


def test_angle_with_horizontal_45():
    assert angle_with_horizontal((0.0, 0.0), (1.0, 1.0)) == pytest.approx(45.0, abs=1e-5)
