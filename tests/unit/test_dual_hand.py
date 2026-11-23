"""Unit tests for DualHandSynthesizer and superpowers."""
import pymunk
import pytest
from src.gestures.detector import GestureType, HandGestureState
from src.game.dual_hand import DualHandSuperpower, DualHandSynthesizer
from src.physics.world import PhysicsWorld


def test_dual_hand_singularity_vortex_trigger():
    """Verify bringing two pinched hands together spawns a SingularityVortex."""
    world = PhysicsWorld(1280, 720)
    synthesizer = DualHandSynthesizer(world)

    hand_a = HandGestureState("Right")
    hand_a.is_pinched = True
    hand_a.screen_pos = (500.0, 300.0)

    hand_b = HandGestureState("Left")
    hand_b.is_pinched = True
    hand_b.screen_pos = (540.0, 300.0)  # Distance = 40px (< 110px)

    events = synthesizer.process_dual_hands([hand_a, hand_b], active_holds=[], now=1.0)
    assert len(events) == 1
    assert events[0].power_type == DualHandSuperpower.SINGULARITY_RIFT
    assert synthesizer.active_singularity is not None
    assert synthesizer.active_singularity.active is True


def test_dual_hand_kamehameha_tidal_wave_trigger():
    """Verify dual open-palm thrust triggers tidal wave superpower."""
    world = PhysicsWorld(1280, 720)
    sphere = world.spawn_sphere(600.0, 400.0)
    synthesizer = DualHandSynthesizer(world)

    hand_a = HandGestureState("Right")
    hand_a.gesture_type = GestureType.PUSH
    hand_a.screen_pos = (500.0, 300.0)

    hand_b = HandGestureState("Left")
    hand_b.gesture_type = GestureType.PUSH
    hand_b.screen_pos = (600.0, 300.0)

    events = synthesizer.process_dual_hands([hand_a, hand_b], active_holds=[], now=5.0)
    assert len(events) == 1
    assert events[0].power_type == DualHandSuperpower.DUAL_TIDAL_WAVE
    # Sphere should receive upward impulse
    assert sphere.velocity.y < 0.0


def test_dual_hand_prop_clash():
    """Verify bringing two held bodies close together triggers Prop Clash."""
    world = PhysicsWorld(1280, 720)
    body_a = world.spawn_sphere(500.0, 300.0)
    body_b = world.spawn_sphere(540.0, 300.0)  # Distance = 40px (< 75px)

    synthesizer = DualHandSynthesizer(world)
    hand_a = HandGestureState("Right")
    hand_b = HandGestureState("Left")

    active_holds = [
        ((500.0, 300.0), body_a, "Right"),
        ((540.0, 300.0), body_b, "Left")
    ]

    events = synthesizer.process_dual_hands([hand_a, hand_b], active_holds=active_holds, now=10.0)
    assert len(events) == 1
    assert events[0].power_type == DualHandSuperpower.PROP_CLASH
    assert events[0].bonus_score == 600
    # Both bodies should have high explosive recoil
    assert body_a.velocity.x < 0.0
    assert body_b.velocity.x > 0.0
