"""Unit tests for KineticShield."""
import pymunk
import pytest
from src.physics.shield import KineticShield


def test_kinetic_shield_activation_and_deactivation():
    """Verify shield adds and removes kinematic body cleanly from Pymunk space."""
    space = pymunk.Space()
    shield = KineticShield(space, radius=50.0)

    assert shield.active is False
    assert shield.body not in space.bodies

    # Activate
    shield.activate((300.0, 400.0))
    assert shield.active is True
    assert shield.position == (300.0, 400.0)
    assert shield.body in space.bodies
    assert shield.shape in space.shapes

    # Move
    shield.update_position((350.0, 420.0))
    assert shield.position == (350.0, 420.0)
    assert shield.body.position.x == 350.0

    # Deactivate
    shield.deactivate()
    assert shield.active is False
    assert shield.body not in space.bodies
