"""Unit tests for ScreenShake effects."""
import pytest
from src.rendering.effects import ScreenShake


def test_screen_shake_trauma_and_decay():
    """Verify adding trauma produces shake offsets and decays cleanly to zero."""
    shake = ScreenShake(max_offset_px=10.0, decay_rate=2.0)
    assert shake.trauma == 0.0

    shake.add_trauma(0.8)
    assert shake.trauma == 0.8

    # Update with 0.1s step -> trauma decays
    ox, oy = shake.update(0.1)
    assert shake.trauma < 0.8
    assert abs(ox) <= 10.0
    assert abs(oy) <= 10.0

    # Step past decay expiration
    shake.update(1.0)
    assert shake.trauma == 0.0
    ox, oy = shake.update(0.1)
    assert (ox, oy) == (0, 0)
