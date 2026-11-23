"""Unit tests for adaptive EMA smoothing and velocity estimation."""
import pytest
from src.gestures.motion import AdaptiveEMASmoother2D, RollingVelocityEstimator


def test_ema_smoother_static_stability():
    """Verify static input stays static without drift."""
    smoother = AdaptiveEMASmoother2D()
    x, y = smoother.filter(100.0, 200.0, timestamp=1.0)
    assert (x, y) == (100.0, 200.0)

    # Additional static samples
    for i in range(10):
        x, y = smoother.filter(100.0, 200.0, timestamp=1.0 + i * 0.016)
        assert abs(x - 100.0) < 1e-4
        assert abs(y - 200.0) < 1e-4


def test_velocity_estimator_linear_motion():
    """Verify constant 1000 px/s motion returns expected velocity vector."""
    estimator = RollingVelocityEstimator(history_size=5, max_velocity=2500.0)

    # Feed 1000 px/s in X axis over 5 frames at 60 FPS (dt = 0.016667s -> dx = 16.667px)
    dt = 1.0 / 60.0
    for frame in range(5):
        t = frame * dt
        x = frame * 1000.0 * dt
        estimator.add_sample(x, 0.0, timestamp=t)

    vx, vy, speed = estimator.get_velocity()
    assert abs(vx - 1000.0) < 5.0
    assert abs(vy) < 1e-3
    assert abs(speed - 1000.0) < 5.0


def test_velocity_estimator_clamping():
    """Verify ludicrous velocity is clamped to max_velocity limit."""
    estimator = RollingVelocityEstimator(history_size=3, max_velocity=2000.0)

    # Sudden jump of 10000 px in 0.01s (speed = 1,000,000 px/s)
    estimator.add_sample(0.0, 0.0, timestamp=0.0)
    estimator.add_sample(10000.0, 0.0, timestamp=0.01)

    vx, vy, speed = estimator.get_velocity()
    assert abs(vx - 2000.0) < 1e-3
    assert speed == 2000.0
