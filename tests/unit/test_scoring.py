"""Unit tests for ScoringEngine."""
import pytest
from src.game.scoring import COMBO_TIERS, ScoringEngine


def test_scoring_engine_initial_state():
    """Verify scoring engine begins at score=0 and multiplier=1.0x."""
    engine = ScoringEngine()
    assert engine.score == 0
    assert engine.combo_multiplier == 1.0
    assert engine.max_combo == 1.0


def test_combo_multiplier_progression():
    """Verify consecutive hits advance multiplier through tiers up to max tier."""
    engine = ScoringEngine()

    for i in range(1, len(COMBO_TIERS)):
        engine.register_hit(base_points=100, impact_speed=200.0, hit_pos=(0, 0), color=(0, 0, 0))
        assert engine.combo_multiplier == COMBO_TIERS[i]

    # Additional hit should remain at max tier (5.0x)
    engine.register_hit(base_points=100, impact_speed=200.0, hit_pos=(0, 0), color=(0, 0, 0))
    assert engine.combo_multiplier == 5.0
    assert engine.max_combo == 5.0


def test_combo_decay_timer():
    """Verify multiplier drops tier by tier when decay timer expires."""
    engine = ScoringEngine()
    # Advance to 2.0x (tier idx 2)
    engine.register_hit(100, 0.0, (0, 0), (0, 0, 0))
    engine.register_hit(100, 0.0, (0, 0), (0, 0, 0))
    assert engine.combo_multiplier == 2.0

    # Step timer past decay threshold (3.5s)
    engine.update(3.6)
    assert engine.combo_multiplier == 1.5

    # Step timer again
    engine.update(3.6)
    assert engine.combo_multiplier == 1.0
