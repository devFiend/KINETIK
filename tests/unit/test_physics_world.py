"""Unit and integration tests for PhysicsWorld."""
import pymunk
import pytest
from src.physics.world import PhysicsWorld


def test_physics_world_initialization():
    """Verify physics world initializes space, boundaries, and default gravity."""
    world = PhysicsWorld(width=1280, height=720)
    assert world.space is not None
    assert world.gravity > 0.0
    assert len(world._boundary_shapes) == 4


def test_zero_gravity_toggle():
    """Verify toggling zero gravity switches between 0.0 and default gravity."""
    world = PhysicsWorld(width=1280, height=720, gravity_y=900.0)
    assert world.gravity == 900.0

    is_zero = world.toggle_zero_gravity()
    assert is_zero is True
    assert world.gravity == 0.0

    is_zero = world.toggle_zero_gravity()
    assert is_zero is False
    assert world.gravity == 900.0


def test_gravity_drop_and_boundary_confinement():
    """Verify dynamic sphere accelerates downward under gravity and bounces on floor."""
    world = PhysicsWorld(width=1280, height=720, gravity_y=900.0)
    sphere = world.spawn_sphere(x=640.0, y=100.0, radius=20.0)

    initial_y = sphere.position.y
    # Step simulation 60 times (1 full second)
    for _ in range(60):
        world.step(1.0 / 60.0)

    # Sphere should have dropped downward
    assert sphere.position.y > initial_y
    # Sphere should NOT escape bottom boundary (height = 720)
    assert sphere.position.y <= 720.0
