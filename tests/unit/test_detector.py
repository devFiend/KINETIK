"""Unit tests for GestureDetector integration."""
import pytest
from src.camera.hand_tracker import HandData, LandmarkPoint
from src.gestures.detector import GestureDetector, GestureType


def test_gesture_detector_tracking():
    """Verify GestureDetector tracks hand and detects pinch transition."""
    detector = GestureDetector(screen_width=1280, screen_height=720)

    # Synthetic open hand
    points_open = [LandmarkPoint(0.5, 0.5, 0.0) for _ in range(21)]
    points_open[4] = LandmarkPoint(0.40, 0.5, 0.0)  # Thumb
    points_open[8] = LandmarkPoint(0.60, 0.5, 0.0)  # Index (dist = 0.20)
    hand_open = HandData(handedness="Right", confidence=0.95, landmarks=points_open)

    states = detector.process_hands([hand_open], now=1.0)
    assert len(states) == 1
    assert states[0].gesture_type == GestureType.HOVER
    assert states[0].is_pinched is False

    # Synthetic pinched hand
    points_pinch = [LandmarkPoint(0.5, 0.5, 0.0) for _ in range(21)]
    points_pinch[4] = LandmarkPoint(0.50, 0.5, 0.0)
    points_pinch[8] = LandmarkPoint(0.52, 0.5, 0.0)  # dist = 0.02
    hand_pinch = HandData(handedness="Right", confidence=0.95, landmarks=points_pinch)

    # Feed twice for debounce
    detector.process_hands([hand_pinch], now=1.02)
    states = detector.process_hands([hand_pinch], now=1.04)

    assert states[0].is_pinched is True
    assert states[0].gesture_type == GestureType.PINCH
