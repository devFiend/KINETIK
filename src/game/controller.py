"""Telekinesis interaction controller: selection, soft grab, kinetic throw, and force push."""
import math
import time
from typing import Dict, List, Optional, Tuple
import pymunk

from src.config import (
    MAX_RELEASE_VELOCITY,
    SELECTION_RADIUS_PX,
    THROW_FORCE_MULTIPLIER,
    TRACKING_LOSS_GRACE_MS,
)
from src.gestures.detector import GestureType, HandGestureState
from src.physics.constraints import TelekineticJoint
from src.physics.world import PhysicsWorld


class HandTelekinesis:
    """Manages telekinetic state, grab constraints, and throws for a single hand."""

    def __init__(self, handedness: str, space: pymunk.Space):
        self.handedness = handedness
        self.space = space

        self.held_body: Optional[pymunk.Body] = None
        self.joint: Optional[TelekineticJoint] = None
        self.hold_start_time: float = 0.0
        self.last_seen_time: float = 0.0
        self.last_cursor_pos: Tuple[float, float] = (0.0, 0.0)

    @property
    def is_holding(self) -> bool:
        return self.held_body is not None and self.joint is not None

    def grab(self, target_body: pymunk.Body, cursor_pos: Tuple[float, float], now: float) -> None:
        """Attach telekinetic spring constraint to target body."""
        if self.is_holding:
            self.release((0.0, 0.0))

        self.held_body = target_body
        self.hold_start_time = now
        self.last_seen_time = now
        self.last_cursor_pos = cursor_pos
        self.joint = TelekineticJoint(self.space, target_body, cursor_pos)

    def release(self, throw_velocity: Tuple[float, float]) -> Optional[pymunk.Body]:
        """Release held body and impart throw velocity vector with multiplier."""
        released_body = self.held_body
        if self.joint:
            self.joint.detach()
            self.joint = None

        if self.held_body:
            vx, vy = throw_velocity
            # Apply throw force multiplier and clamp
            speed = math.hypot(vx, vy)
            if speed > 0:
                boosted_speed = min(MAX_RELEASE_VELOCITY, speed * THROW_FORCE_MULTIPLIER)
                scale = boosted_speed / speed
                self.held_body.velocity = pymunk.Vec2d(vx * scale, vy * scale)

            self.held_body = None

        return released_body


class TelekinesisController:
    """
    High-level telekinesis coordinator: proximity body selection, grab locking,
    flick-to-throw release, and open-palm force push shockwaves.
    """

    def __init__(self, physics_world: PhysicsWorld, selection_radius: float = SELECTION_RADIUS_PX):
        self.physics_world = physics_world
        self.selection_radius = selection_radius
        self._hands: Dict[str, HandTelekinesis] = {}

    def _get_hand_telekinesis(self, handedness: str) -> HandTelekinesis:
        if handedness not in self._hands:
            self._hands[handedness] = HandTelekinesis(handedness, self.physics_world.space)
        return self._hands[handedness]

    def find_nearest_body(self, cursor_pos: Tuple[float, float]) -> Tuple[Optional[pymunk.Body], float]:
        """Find the closest dynamic rigid body within selection radius."""
        cx, cy = cursor_pos
        nearest_body: Optional[pymunk.Body] = None
        min_distance = float("inf")

        for body in self.physics_world.get_dynamic_bodies():
            bx, by = body.position.x, body.position.y
            dist = math.hypot(bx - cx, by - cy)
            if dist <= self.selection_radius and dist < min_distance:
                min_distance = dist
                nearest_body = body

        return nearest_body, min_distance

    def update(self, gesture_states: List[HandGestureState], now: Optional[float] = None) -> None:
        """
        Process gesture states for active hands to manage grab, hold, throw, and push.
        """
        t = now if now is not None else time.time()
        active_handedness = set()

        for state in gesture_states:
            active_handedness.add(state.handedness)
            tk = self._get_hand_telekinesis(state.handedness)
            tk.last_seen_time = t
            tk.last_cursor_pos = state.screen_pos

            # 1. Grab Trigger: Just pinched near an interactable object
            if state.just_pinched and not tk.is_holding:
                nearest_body, dist = self.find_nearest_body(state.screen_pos)
                if nearest_body:
                    tk.grab(nearest_body, state.screen_pos, t)

            # 2. Hold Update: Update kinematic anchor position
            elif tk.is_holding and state.is_pinched:
                tk.joint.update_hand_position(state.screen_pos)

            # 3. Release / Throw Trigger: Pinch released while holding
            elif tk.is_holding and (state.just_released or not state.is_pinched):
                tk.release(state.velocity)

            # 4. Force Push Shockwave: Rapid open palm thrust
            elif state.gesture_type == GestureType.PUSH and not tk.is_holding:
                self._apply_force_push(state.screen_pos, push_radius=250.0, impulse_strength=800.0)

        # 5. Handle tracking dropout grace period for missing hands
        for handedness, tk in self._hands.items():
            if handedness not in active_handedness and tk.is_holding:
                elapsed_dropout = (t - tk.last_seen_time) * 1000.0
                if elapsed_dropout > TRACKING_LOSS_GRACE_MS:
                    # Grace period expired -> safely release without violent throw
                    tk.release((0.0, 0.0))

    def _apply_force_push(
        self,
        origin: Tuple[float, float],
        push_radius: float = 250.0,
        impulse_strength: float = 800.0
    ) -> int:
        """Cast radial impulse wave repelling unheld nearby dynamic bodies."""
        ox, oy = origin
        affected_count = 0

        for body in self.physics_world.get_dynamic_bodies():
            bx, by = body.position.x, body.position.y
            dx = bx - ox
            dy = by - oy
            dist = math.hypot(dx, dy)

            if 10.0 < dist <= push_radius:
                # Radial impulse scaled by distance
                factor = (1.0 - dist / push_radius) * impulse_strength
                nx, ny = dx / dist, dy / dist
                body.apply_impulse_at_world_point(
                    pymunk.Vec2d(nx * factor * body.mass, ny * factor * body.mass),
                    body.position
                )
                affected_count += 1

        return affected_count

    def get_active_holds(self) -> List[Tuple[Tuple[float, float], pymunk.Body, str]]:
        """Returns list of currently held objects: (cursor_pos, body, handedness)."""
        holds = []
        for handedness, tk in self._hands.items():
            if tk.is_holding:
                holds.append((tk.last_cursor_pos, tk.held_body, handedness))
        return holds
