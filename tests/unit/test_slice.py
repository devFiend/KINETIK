"""Unit tests for KineticBlade gesture slicing physics engine."""
import pymunk
import pytest
from src.gestures.detector import HandGestureState
from src.physics.objects import PropType
from src.physics.slice import KineticBlade
from src.physics.targets import TargetDrone
from src.physics.world import PhysicsWorld


def test_kinetic_blade_sphere_bisecting():
    """Verify rapid karate chop splits dynamic sphere into two smaller spheres."""
    world = PhysicsWorld(1280, 720)
    blade = KineticBlade(world.space)

    # Spawn sphere right in the slice trajectory: (500, 300)
    sphere = world.spawn_sphere(500.0, 300.0, radius=28.0)
    initial_bodies = len(world.get_dynamic_bodies())

    # Hand moving rapidly from (450, 300) to (550, 300) -> speed 1600 px/s
    hand = HandGestureState("Right")
    hand.is_pinched = False
    hand.screen_pos = (550.0, 300.0)
    hand.velocity = (1600.0, 0.0)
    hand.speed = 1600.0

    results = blade.process_hand_slicing(hand, dt=1.0 / 60.0, now=1.0)

    assert len(results) == 1
    cut = results[0]
    assert cut.sliced_target is False
    assert len(cut.new_bodies) == 2
    # Original sphere was replaced by 2 smaller spheres
    new_bodies = world.get_dynamic_bodies()
    assert len(new_bodies) == initial_bodies + 1
    for nb in cut.new_bodies:
        assert nb.custom_data.prop_type == PropType.SPHERE
        assert nb.custom_data.radius < 28.0


def test_kinetic_blade_target_drone_destruction():
    """Verify blade strike shatters target drone instantly."""
    world = PhysicsWorld(1280, 720)
    blade = KineticBlade(world.space)

    target = TargetDrone(world.space, 500.0, 300.0)
    assert target.alive is True

    hand = HandGestureState("Right")
    hand.is_pinched = False
    hand.screen_pos = (550.0, 300.0)
    hand.velocity = (1400.0, 0.0)
    hand.speed = 1400.0

    results = blade.process_hand_slicing(hand, dt=1.0 / 60.0, now=1.0)

    assert len(results) == 1
    assert results[0].sliced_target is True
    assert target.alive is False
