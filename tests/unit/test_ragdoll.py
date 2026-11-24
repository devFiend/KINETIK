"""Unit tests for Articulated Ragdoll physics and RagdollGodMode."""
import pymunk
import pytest
from src.game.ragdoll_mode import RagdollGodMode
from src.game.scoring import ScoringEngine
from src.physics.contraptions import PinballBumper, PortalPair, Trampoline
from src.physics.ragdoll import Ragdoll, RagdollExpression
from src.physics.world import PhysicsWorld


def test_ragdoll_skeleton_and_joint_hierarchy():
    """Verify ragdoll creates complete 10-body articulated skeleton with limits."""
    world = PhysicsWorld(1280, 720)
    rag = Ragdoll(world.space, 600.0, 300.0)

    # Must contain Head, Torso, 4 Arm segments, 4 Leg segments = 10 bodies
    assert len(rag.bodies) == 10
    assert len(rag.shapes) == 10
    # Must contain neck, 2 shoulders, 2 elbows, 2 hips, 2 knees = 9 pivots + limits = 18 constraints
    assert len(rag.joints) >= 14

    # Verify self-collision grouping
    filter_group = rag.filter.group
    for s in rag.shapes:
        assert s.filter.group == filter_group

    rag.destroy()
    assert len(rag.bodies) == 0


def test_ragdoll_emotional_expression_transitions():
    """Verify facial expressions adapt to speed, grabs, and impact trauma."""
    world = PhysicsWorld(1280, 720)
    rag = Ragdoll(world.space, 600.0, 300.0)

    # Initial resting state
    rag.update(0.016)
    assert rag.expression == RagdollExpression.HAPPY

    # High speed flinging triggers panic scream
    rag.torso.velocity = pymunk.Vec2d(800.0, 0.0)
    rag.update(0.016)
    assert rag.expression == RagdollExpression.PANIC_SCREAM

    # Hard impact triggers dizzy expression and awards coins
    coins = rag.register_impact(500.0)
    assert coins > 0
    assert rag.expression == RagdollExpression.DIZZY

    # Telekinetic hold flag
    rag.dizzy_timer = 0.0
    rag.torso.velocity = pymunk.Vec2d(0.0, 0.0)
    rag.torso.custom_data.is_held = True
    rag.update(0.016)
    assert rag.expression == RagdollExpression.GRABBED


def test_pinball_bumper_repulsion():
    """Verify pinball bumper violently repels colliding bodies."""
    world = PhysicsWorld(1280, 720)
    bumper = PinballBumper(world.space, 500.0, 300.0, bounce_impulse=1200.0)

    body = world.spawn_sphere(540.0, 300.0)
    contact = bumper.trigger_hit(body)

    assert bumper.hit_count == 1
    assert bumper.flash_timer > 0.0
    assert body.velocity.x > 500.0  # Repelled to the right


def test_wormhole_portal_teleportation():
    """Verify dynamic bodies entering Portal A instantly emerge from Portal B."""
    world = PhysicsWorld(1280, 720)
    portals = PortalPair(pos_a=(200.0, 300.0), pos_b=(1000.0, 300.0), radius=40.0)

    ball = world.spawn_sphere(210.0, 300.0)  # Near Portal A
    ball.velocity = pymunk.Vec2d(-400.0, 0.0)

    jumps = portals.update_and_teleport([ball], dt=0.016, now=1.0)
    assert len(jumps) == 1
    # Emerging position should now be at Portal B (1000, 300)
    assert ball.position.x >= 950.0


def test_ragdoll_god_mode_lifecycle():
    """Verify full RagdollGodMode starts, tracks combo, and updates clean."""
    world = PhysicsWorld(1280, 720)
    scoring = ScoringEngine()
    mode = RagdollGodMode(world, scoring)

    mode.start()
    assert mode.ragdoll is not None
    assert len(mode.bumpers) == 3
    assert mode.portals is not None
    assert mode.trampoline is not None
    assert mode.coins == 0
    assert mode.combo == 1.0

    mode.update(0.1)
    mode.reset()
    assert mode.coins == 0
