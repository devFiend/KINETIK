"""Unit tests for ObjectFactory and prop creation."""
import pymunk
import pytest
from src.physics.objects import ObjectFactory, PropType
from src.physics.world import PhysicsWorld


def test_object_factory_sphere_creation():
    """Verify ObjectFactory creates sphere with correct mass, radius, and metadata."""
    world = PhysicsWorld(width=800, height=600)
    sphere = ObjectFactory.create_sphere(world.space, 400.0, 300.0, radius=25.0, mass=1.5)

    assert sphere.body_type == pymunk.Body.DYNAMIC
    assert sphere.mass == 1.5
    assert sphere.position.x == 400.0
    assert sphere.position.y == 300.0
    assert hasattr(sphere, "custom_data")
    assert sphere.custom_data.prop_type == PropType.SPHERE
    assert sphere.custom_data.radius == 25.0


def test_object_factory_box_creation():
    """Verify ObjectFactory creates box with correct dimensions and metadata."""
    world = PhysicsWorld(width=800, height=600)
    box = ObjectFactory.create_box(world.space, 200.0, 150.0, width=40.0, height=40.0, mass=2.0)

    assert box.body_type == pymunk.Body.DYNAMIC
    assert box.mass == 2.0
    assert box.custom_data.prop_type == PropType.BOX
    assert box.custom_data.width == 40.0


def test_clear_and_reset_playground():
    """Verify resetting playground spawns starter set and clears properly."""
    world = PhysicsWorld(width=1280, height=720)
    world.reset_default_playground()

    dynamic_bodies = world.get_dynamic_bodies()
    assert len(dynamic_bodies) == 5

    world.clear_dynamic_bodies()
    assert len(world.get_dynamic_bodies()) == 0
