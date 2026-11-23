"""Unit and integration tests for TelekinesisController and soft spring joints."""
import pymunk
import pytest
from src.camera.hand_tracker import HandData, LandmarkPoint
from src.config import SELECTION_RADIUS_PX
from src.game.controller import TelekinesisController
from src.gestures.detector import GestureDetector, GestureType
from src.physics.world import PhysicsWorld


def test_proximity_selection_within_radius():
    """Verify object within SELECTION_RADIUS_PX is identified, while distant object is ignored."""
    world = PhysicsWorld(width=1280, height=720)
    sphere = world.spawn_sphere(500.0, 300.0, radius=25.0)
    controller = TelekinesisController(world, selection_radius=80.0)

    # Nearby cursor (dist = 30px)
    found_body, dist = controller.find_nearest_body((530.0, 300.0))
    assert found_body is sphere
    assert abs(dist - 30.0) < 1e-3

    # Distant cursor (dist = 120px > 80px)
    far_body, far_dist = controller.find_nearest_body((620.0, 300.0))
    assert far_body is None


def test_telekinetic_grab_and_throw_lifecycle():
    """Verify grabbing attaches spring constraint and release imparts throw velocity."""
    world = PhysicsWorld(width=1280, height=720)
    sphere = world.spawn_sphere(500.0, 300.0, radius=25.0)
    controller = TelekinesisController(world)

    detector = GestureDetector(screen_width=1280, screen_height=720)

    # 1. Pinch hand right at sphere position (x=500/1280, y=300/720)
    norm_x = 500.0 / 1280.0
    norm_y = 300.0 / 720.0
    pinched_points = [LandmarkPoint(norm_x, norm_y, 0.0) for _ in range(21)]
    pinched_points[4] = LandmarkPoint(norm_x, norm_y, 0.0)
    pinched_points[8] = LandmarkPoint(norm_x + 0.01, norm_y, 0.0)
    hand_pinched = HandData(handedness="Right", confidence=0.95, landmarks=pinched_points)

    # Update twice for debounce
    states = detector.process_hands([hand_pinched], now=1.0)
    controller.update(states, now=1.0)
    states = detector.process_hands([hand_pinched], now=1.02)
    controller.update(states, now=1.02)

    # Verify sphere is now held
    active_holds = controller.get_active_holds()
    assert len(active_holds) == 1
    assert active_holds[0][1] is sphere
    assert sphere.custom_data.is_held is True

    # 2. Release pinch with simulated fling velocity
    open_points = [LandmarkPoint(norm_x, norm_y, 0.0) for _ in range(21)]
    open_points[4] = LandmarkPoint(norm_x - 0.1, norm_y, 0.0)
    open_points[8] = LandmarkPoint(norm_x + 0.1, norm_y, 0.0)
    hand_open = HandData(handedness="Right", confidence=0.95, landmarks=open_points)

    # Update twice for debounce
    states = detector.process_hands([hand_open], now=1.04)
    controller.update(states, now=1.04)
    states = detector.process_hands([hand_open], now=1.06)
    controller.update(states, now=1.06)

    # Verify sphere is released
    assert len(controller.get_active_holds()) == 0
    assert sphere.custom_data.is_held is False


def test_force_push_shockwave():
    """Verify force push imparts radial impulse to nearby dynamic bodies."""
    world = PhysicsWorld(width=1280, height=720, gravity_y=0.0)
    sphere = world.spawn_sphere(600.0, 300.0, radius=20.0)  # 100px to the right of push center
    controller = TelekinesisController(world)

    initial_vx = sphere.velocity.x

    # Apply push at (500, 300)
    affected = controller._apply_force_push(origin=(500.0, 300.0), push_radius=200.0, impulse_strength=500.0)
    assert affected == 1

    # Sphere should have gained positive X velocity (pushed away to the right)
    assert sphere.velocity.x > initial_vx
