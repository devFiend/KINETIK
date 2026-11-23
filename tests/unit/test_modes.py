"""Unit and integration tests for Game Modes and Target Rush."""
import pytest
from src.game.modes import FreePlayMode, GameModeState, ModeType, TargetRushMode
from src.game.scoring import ScoringEngine
from src.physics.world import PhysicsWorld


def test_free_play_mode_lifecycle():
    """Verify Free Play starts in PLAYING state and can be reset."""
    world = PhysicsWorld(1280, 720)
    scoring = ScoringEngine()
    mode = FreePlayMode(world, scoring)

    mode.start()
    assert mode.state == GameModeState.PLAYING
    assert len(world.get_dynamic_bodies()) == 5

    mode.reset()
    assert len(world.get_dynamic_bodies()) == 5


def test_target_rush_mode_timer_and_round_over():
    """Verify Target Rush counts down and transitions to ROUND_OVER at 0s."""
    world = PhysicsWorld(1280, 720)
    scoring = ScoringEngine()
    mode = TargetRushMode(world, scoring, round_duration_sec=10.0)

    mode.start()
    assert mode.state == GameModeState.PLAYING
    assert mode.time_remaining == 10.0
    assert len(mode.targets) == 2

    # Advance time by 5 seconds
    mode.update(5.0)
    assert abs(mode.time_remaining - 5.0) < 1e-3
    assert mode.state == GameModeState.PLAYING

    # Advance past 10 seconds -> ROUND_OVER
    mode.update(5.5)
    assert mode.time_remaining == 0.0
    assert mode.state == GameModeState.ROUND_OVER
