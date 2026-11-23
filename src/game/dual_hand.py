"""Dual-hand synthesis coordinator: prop clashing, Kamehameha tidal wave, and singularity rifts."""
from dataclasses import dataclass
from enum import Enum, auto
import math
import time
from typing import List, Optional, Tuple
import pymunk

from src.gestures.detector import GestureType, HandGestureState
from src.physics.shield import KineticShield
from src.physics.singularity import SingularityVortex
from src.physics.world import PhysicsWorld


class DualHandSuperpower(Enum):
    NONE = auto()
    PROP_CLASH = auto()
    DUAL_TIDAL_WAVE = auto()
    SINGULARITY_RIFT = auto()
    SHIELD_DEFLECTION = auto()


@dataclass
class DualHandEvent:
    """Telemetry describing an executed multi-hand superpower."""
    power_type: DualHandSuperpower
    position: Tuple[float, float]
    bonus_score: int
    screen_shake_trauma: float


class DualHandSynthesizer:
    """
    Coordinates multi-hand combos:
    1. Prop Clash: Smashing two held objects into each other mid-air.
    2. Kamehameha Tidal Wave: Dual open palms thrusting forward together.
    3. Singularity Vortex: Bringing two closed pinches together to spawn a black hole attractor.
    4. Kinetic Shield: Flat non-dominant palm deflection field.
    """

    def __init__(self, physics_world: PhysicsWorld):
        self.physics_world = physics_world
        self.shield = KineticShield(physics_world.space)
        self.active_singularity: Optional[SingularityVortex] = None
        self.last_superpower_time: float = -999.0
        self.cooldown_sec: float = 2.0

    def process_dual_hands(
        self,
        active_states: List[HandGestureState],
        active_holds: List[Tuple[Tuple[float, float], pymunk.Body, str]],
        now: Optional[float] = None
    ) -> List[DualHandEvent]:
        """
        Evaluate multi-hand poses and trigger superpowers.
        """
        t = now if now is not None else time.time()
        events: List[DualHandEvent] = []

        # 1. Update active Singularity Vortex if running
        if self.active_singularity:
            dynamic_bodies = self.physics_world.get_dynamic_bodies()
            still_active = self.active_singularity.update(1.0 / 60.0, dynamic_bodies)
            if not still_active:
                self.active_singularity = None

        if len(active_states) < 2:
            self.shield.deactivate()
            return events

        hand_a = active_states[0]
        hand_b = active_states[1]

        ax, ay = hand_a.screen_pos
        bx, by = hand_b.screen_pos
        hands_dist = math.hypot(ax - bx, ay - by)
        midpoint = ((ax + bx) * 0.5, (ay + by) * 0.5)

        # --- Superpower 1: Mid-Air Prop Clash ---
        # When both hands are holding an object, and they accelerate towards each other
        if len(active_holds) >= 2:
            body_a = active_holds[0][1]
            body_b = active_holds[1][1]
            if body_a is not body_b:
                dist_bodies = math.hypot(
                    body_a.position.x - body_b.position.x,
                    body_a.position.y - body_b.position.y
                )
                if dist_bodies < 75.0:
                    # Detonate Clash!
                    clash_pos = (
                        (body_a.position.x + body_b.position.x) * 0.5,
                        (body_a.position.y + body_b.position.y) * 0.5
                    )
                    # Impart high-speed explosive recoil to both bodies
                    body_a.velocity = pymunk.Vec2d(-1600.0, -900.0)
                    body_b.velocity = pymunk.Vec2d(1600.0, -900.0)

                    # Radial shockwave to all other props
                    for body in self.physics_world.get_dynamic_bodies():
                        if body not in (body_a, body_b):
                            dx = body.position.x - clash_pos[0]
                            dy = body.position.y - clash_pos[1]
                            d = math.hypot(dx, dy)
                            if 5.0 < d < 350.0:
                                impulse = (1.0 - d / 350.0) * 1200.0
                                body.apply_impulse_at_world_point(
                                    pymunk.Vec2d(dx / d * impulse, dy / d * impulse),
                                    body.position
                                )

                    events.append(DualHandEvent(
                        power_type=DualHandSuperpower.PROP_CLASH,
                        position=clash_pos,
                        bonus_score=600,
                        screen_shake_trauma=0.75
                    ))
                    return events

        # --- Superpower 2: Gravitational Singularity Rift ---
        # Both hands pinched and brought close together (< 110px)
        if hand_a.is_pinched and hand_b.is_pinched and hands_dist < 110.0:
            if not self.active_singularity and (t - self.last_superpower_time >= self.cooldown_sec):
                self.last_superpower_time = t
                self.active_singularity = SingularityVortex(
                    self.physics_world.space,
                    center=midpoint,
                    duration=3.5,
                    pull_radius=420.0
                )
                events.append(DualHandEvent(
                    power_type=DualHandSuperpower.SINGULARITY_RIFT,
                    position=midpoint,
                    bonus_score=350,
                    screen_shake_trauma=0.45
                ))

        # --- Superpower 3: Kamehameha Dual Tidal Wave ---
        # Both hands pushing forward at high velocity with open palms
        elif hand_a.gesture_type == GestureType.PUSH and hand_b.gesture_type == GestureType.PUSH:
            if t - self.last_superpower_time >= 1.5:
                self.last_superpower_time = t
                # Screen-clearing impulse wave
                for body in self.physics_world.get_dynamic_bodies():
                    body.apply_impulse_at_world_point(
                        pymunk.Vec2d(0.0, -1400.0 * body.mass),
                        body.position
                    )
                events.append(DualHandEvent(
                    power_type=DualHandSuperpower.DUAL_TIDAL_WAVE,
                    position=midpoint,
                    bonus_score=400,
                    screen_shake_trauma=0.60
                ))

        # --- Superpower 4: Kinetic Shield ---
        # If one hand is hovering flat while other hand is active, project shield on non-dominant hand
        shield_candidate = None
        for state in active_states:
            if not state.is_pinched and state.speed < 250.0 and state.gesture_type == GestureType.HOVER:
                shield_candidate = state
                break

        if shield_candidate:
            self.shield.activate(shield_candidate.screen_pos)
        else:
            self.shield.deactivate()

        return events
