"""Unit and headless tests for MediaPipe HandTracker."""
import numpy as np
import pytest
from src.camera.hand_tracker import HandTracker, LandmarkPoint, HandData, HAND_CONNECTIONS


def test_hand_connections_integrity():
    """Verify standard hand connections pair valid 21-joint indices [0..20]."""
    assert len(HAND_CONNECTIONS) == 21
    for start, end in HAND_CONNECTIONS:
        assert 0 <= start <= 20
        assert 0 <= end <= 20
        assert start != end


def test_hand_tracker_blank_frame_inference():
    """Verify hand tracker processes blank frames without crashing and returns zero hands."""
    tracker = HandTracker()
    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    hands = tracker.process_frame(blank_frame)
    assert isinstance(hands, list)
    assert len(hands) == 0

    tracker.close()


def test_hand_data_dataclass_properties():
    """Verify HandData convenience properties (wrist, thumb_tip, index_tip, hand_center)."""
    # 21 synthetic dummy points
    points = [LandmarkPoint(x=float(i) * 0.01, y=float(i) * 0.02, z=0.0) for i in range(21)]
    hand = HandData(handedness="Right", confidence=0.95, landmarks=points)

    assert hand.wrist == points[0]
    assert hand.thumb_tip == points[4]
    assert hand.index_tip == points[8]

    center = hand.hand_center
    expected_x = (points[0].x + points[9].x) * 0.5
    expected_y = (points[0].y + points[9].y) * 0.5
    assert abs(center.x - expected_x) < 1e-6
    assert abs(center.y - expected_y) < 1e-6
