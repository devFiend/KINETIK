"""Unit tests for PinchDetector and Schmitt-trigger hysteresis."""
import pytest
from src.camera.hand_tracker import LandmarkPoint
from src.gestures.pinch import PinchDetector


def test_pinch_detector_threshold_hysteresis():
    """Verify pinch enters at enter_threshold (0.055) and exits at exit_threshold (0.085)."""
    detector = PinchDetector(enter_threshold=0.055, exit_threshold=0.085, debounce_frames=2)
    assert detector.is_pinched is False

    # Start open (dist = 0.15)
    t = LandmarkPoint(0.5, 0.5, 0.0)
    i = LandmarkPoint(0.65, 0.5, 0.0)
    is_p, _, _ = detector.update(t, i)
    assert is_p is False

    # Move to borderline 0.07 (inside hysteresis deadzone; should remain False)
    i = LandmarkPoint(0.57, 0.5, 0.0)
    is_p, _, _ = detector.update(t, i)
    assert is_p is False

    # Move below enter threshold 0.04 (frame 1 candidate)
    i = LandmarkPoint(0.54, 0.5, 0.0)
    is_p, _, _ = detector.update(t, i)
    assert is_p is False, "Debounce requires 2 consecutive frames"

    # Frame 2 candidate confirmed -> is_pinched becomes True
    is_p, just_p, _ = detector.update(t, i)
    assert is_p is True
    assert just_p is True

    # Move back into deadzone 0.075 -> should remain True due to hysteresis
    i = LandmarkPoint(0.575, 0.5, 0.0)
    is_p, _, _ = detector.update(t, i)
    assert is_p is True

    # Move above exit threshold 0.095 (frame 1 candidate exit)
    i = LandmarkPoint(0.595, 0.5, 0.0)
    is_p, _, _ = detector.update(t, i)
    assert is_p is True, "Exit debounce requires 2 consecutive frames"

    # Frame 2 confirmed exit -> is_pinched becomes False
    is_p, _, just_r = detector.update(t, i)
    assert is_p is False
    assert just_r is True


def test_pinch_factor_interpolation():
    """Verify pinch factor smoothly normalizes from 0.0 to 1.0."""
    detector = PinchDetector(enter_threshold=0.05, exit_threshold=0.08)
    t = LandmarkPoint(0.5, 0.5, 0.0)

    # Wide open (dist = 0.25 -> clamped to 0.0)
    i = LandmarkPoint(0.75, 0.5, 0.0)
    detector.update(t, i)
    assert detector.get_pinch_factor() == 0.0

    # Fully pinched (dist = 0.03 -> clamped to 1.0)
    i = LandmarkPoint(0.53, 0.5, 0.0)
    detector.update(t, i)
    assert detector.get_pinch_factor() == 1.0
