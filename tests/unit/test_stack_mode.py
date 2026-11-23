"""Unit tests for TheStackMode (Zen Tower Balancing Mode)."""
import pymunk
import pytest
from src.game.scoring import ScoringEngine
from src.game.stack_mode import CHECKPOINT_ALTITUDES, HOLD_DURATION_REQUIRED, TheStackMode
from src.physics.world import PhysicsWorld


def test_stack_mode_initialization():
    """Verify foundation base and staging props spawn on start."""
    world = PhysicsWorld(1280, 720)
    scoring = ScoringEngine()
    mode = TheStackMode(world, scoring)

    mode.start()
    assert mode.current_tier == 1
    assert mode.hold_timer == 0.0
    assert mode.hold_progress == 0.0

    bodies = world.get_dynamic_bodies()
    assert len(bodies) >= 3  # Foundation plank + staging items


def test_stack_mode_altitude_and_hold_progression():
    """Verify holding stable height advances checkpoint tier."""
    world = PhysicsWorld(1280, 720)
    scoring = ScoringEngine()
    mode = TheStackMode(world, scoring)
    mode.start()

    # Clear bodies and spawn a tall static stack in the center zone
    world.clear_dynamic_bodies()
    floor_y = 710.0
    cx = 640.0

    # Target tier 1 is 160px altitude, so box top needs to reach 710 - 170 = 540
    # Center y = 570, height = 60 -> top = 540 -> altitude = 170px
    b = world.spawn_box(cx, 570.0, size=60.0)
    b.velocity = pymunk.Vec2d(0.0, 0.0)

    alt, stable = mode._measure_tower()
    assert alt >= 160.0
    assert stable is True

    # Advance time past hold threshold
    mode.update(HOLD_DURATION_REQUIRED + 0.1)
    assert mode.current_tier == 2
    assert mode.recent_checkpoint_event is not None
    assert mode.recent_checkpoint_event.tier == 1
    assert scoring.score > 0
