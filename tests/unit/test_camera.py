"""Unit and headless tests for WebcamCapture module."""
import time
import numpy as np
import pytest
from src.camera.webcam import WebcamCapture


def test_mock_webcam_initialization():
    """Verify mock camera initializes, produces frames, and tracks FPS cleanly."""
    cam = WebcamCapture(width=320, height=240, mock_mode=True)
    assert cam.start() is True
    assert cam.is_available is True

    # Allow worker thread to produce initial frames
    time.sleep(0.1)

    frame, ts = cam.get_latest_frame()
    assert frame is not None
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (240, 320, 3)
    assert ts > 0.0

    cam.stop()
    assert cam._running is False


def test_webcam_mirror_toggle():
    """Verify mirror toggle switches state."""
    cam = WebcamCapture(mirror=True, mock_mode=True)
    assert cam.mirror is True
    cam.toggle_mirror()
    assert cam.mirror is False
    cam.toggle_mirror()
    assert cam.mirror is True
