"""Kinetic Blade: Gesture slicing physics engine for high-speed telekinetic cutting."""
from dataclasses import dataclass
import math
import time
from typing import List, Optional, Set, Tuple
import pymunk

from src.config import (
    COLOR_CYAN_GLOW,
    COLOR_GOLD_AMBER,
    COLOR_HAZARD_RED,
    COLOR_WHITE_BRIGHT,
)
from src.gestures.detector import HandGestureState
from src.physics.objects import ObjectFactory, PropType, PropVisualData
from src.physics.targets import TargetDrone


SLICE_MIN_SPEED_PX = 1000.0  # Swipe speed required to ignite kinetic blade
MIN_SPLIT_RADIUS = 16.0       # Minimum sphere radius that can be bisected
MIN_SPLIT_BOX_SIZE = 26.0     # Minimum box dimension that can be bisected


@dataclass
class SliceCutResult:
    """Telemetry produced by a single blade cut."""
    p1: Tuple[float, float]
    p2: Tuple[float, float]
    cut_point: Tuple[float, float]
    sliced_target: bool
    new_bodies: List[pymunk.Body]
    bonus_score: int


class KineticBlade:
    """
    High-speed gesture slicing engine.
    Detects supersonic karate chops and knife-hand swipes, raycasting cutting planes
    through dynamic props and target drones.
    """

    def __init__(self, space: pymunk.Space):
        self.space = space
        self.last_slice_time: float = 0.0
        self.cooldown_sec: float = 0.10  # 100ms cut cooldown to prevent duplicate frame hits
        self.active_trails: List[Tuple[Tuple[float, float], Tuple[float, float], float]] = []

    def update_trails(self, dt: float) -> None:
        """Fade out visual neon blade trails."""
        updated = []
        for p1, p2, alpha in self.active_trails:
            new_alpha = alpha - dt * 4.0  # ~250ms life
            if new_alpha > 0.0:
                updated.append((p1, p2, new_alpha))
        self.active_trails = updated

    def process_hand_slicing(
        self,
        hand_state: HandGestureState,
        dt: float,
        now: Optional[float] = None
    ) -> List[SliceCutResult]:
        """
        Evaluate a single hand's trajectory and perform slicing if speed threshold is exceeded.
        """
        t = now if now is not None else time.time()
        results: List[SliceCutResult] = []

        # Must not be pinched and must be swiping fast
        if hand_state.is_pinched or hand_state.speed < SLICE_MIN_SPEED_PX:
            return results

        if t - self.last_slice_time < self.cooldown_sec:
            return results

        vx, vy = hand_state.velocity
        curr_x, curr_y = hand_state.screen_pos
        # Project previous position from velocity vector
        prev_x = curr_x - vx * max(dt, 1.0 / 60.0)
        prev_y = curr_y - vy * max(dt, 1.0 / 60.0)

        p1 = pymunk.Vec2d(prev_x, prev_y)
        p2 = pymunk.Vec2d(curr_x, curr_y)
        cut_len = (p2 - p1).length

        if cut_len < 10.0:
            return results

        # Register trail for neon laser rendering
        self.active_trails.append(((p1.x, p1.y), (p2.x, p2.y), 1.0))

        # Perform segment query against physics space
        queries = self.space.segment_query(p1, p2, radius=12.0, shape_filter=pymunk.ShapeFilter())
        if not queries:
            return results

        # Normal vector perpendicular to slice trajectory
        slice_dir = (p2 - p1).normalized()
        perp_dir = pymunk.Vec2d(-slice_dir.y, slice_dir.x)

        sliced_bodies: Set[pymunk.Body] = set()

        for info in queries:
            shape = info.shape
            body = shape.body
            if not body or body.body_type == pymunk.Body.STATIC or body in sliced_bodies:
                continue

            hit_point = (info.point.x, info.point.y)
            sliced_bodies.add(body)

            # Check if hitting a TargetDrone
            target_drone: Optional[TargetDrone] = getattr(body, "target_ref", None)
            if target_drone and target_drone.alive:
                target_drone.destroy()
                self.last_slice_time = t
                results.append(SliceCutResult(
                    p1=(p1.x, p1.y),
                    p2=(p2.x, p2.y),
                    cut_point=hit_point,
                    sliced_target=True,
                    new_bodies=[],
                    bonus_score=350
                ))
                continue

            # Check dynamic prop bisecting
            visual_data: Optional[PropVisualData] = getattr(body, "custom_data", None)
            if not visual_data:
                continue

            orig_pos = body.position
            orig_vel = body.velocity

            if visual_data.prop_type == PropType.SPHERE and visual_data.radius >= MIN_SPLIT_RADIUS:
                new_radius = max(14.0, visual_data.radius * 0.707)
                half_mass = max(0.4, body.mass * 0.5)

                # Remove original sphere
                self._remove_body(body)

                # Spawn 2 split spheres
                offset = perp_dir * (new_radius * 0.8)
                b1 = ObjectFactory.create_sphere(
                    self.space,
                    orig_pos.x + offset.x,
                    orig_pos.y + offset.y,
                    radius=new_radius,
                    mass=half_mass,
                    primary_color=visual_data.primary_color
                )
                b2 = ObjectFactory.create_sphere(
                    self.space,
                    orig_pos.x - offset.x,
                    orig_pos.y - offset.y,
                    radius=new_radius,
                    mass=half_mass,
                    primary_color=visual_data.primary_color
                )

                # Impart explosive lateral slice momentum
                b1.velocity = orig_vel + perp_dir * 500.0
                b2.velocity = orig_vel - perp_dir * 500.0

                self.last_slice_time = t
                results.append(SliceCutResult(
                    p1=(p1.x, p1.y),
                    p2=(p2.x, p2.y),
                    cut_point=hit_point,
                    sliced_target=False,
                    new_bodies=[b1, b2],
                    bonus_score=150
                ))

            elif visual_data.prop_type == PropType.BOX and (visual_data.width >= MIN_SPLIT_BOX_SIZE or visual_data.height >= MIN_SPLIT_BOX_SIZE):
                # Cut box along whichever axis is larger
                w = visual_data.width
                h = visual_data.height
                half_mass = max(0.5, body.mass * 0.5)

                self._remove_body(body)

                if w >= h:
                    new_w = w * 0.5
                    new_h = h
                    offset = perp_dir * (new_w * 0.6)
                else:
                    new_w = w
                    new_h = h * 0.5
                    offset = perp_dir * (new_h * 0.6)

                b1 = ObjectFactory.create_box(
                    self.space,
                    orig_pos.x + offset.x,
                    orig_pos.y + offset.y,
                    width=new_w,
                    height=new_h,
                    mass=half_mass,
                    primary_color=visual_data.primary_color
                )
                b2 = ObjectFactory.create_box(
                    self.space,
                    orig_pos.x - offset.x,
                    orig_pos.y - offset.y,
                    width=new_w,
                    height=new_h,
                    mass=half_mass,
                    primary_color=visual_data.primary_color
                )

                b1.velocity = orig_vel + perp_dir * 450.0
                b2.velocity = orig_vel - perp_dir * 450.0

                self.last_slice_time = t
                results.append(SliceCutResult(
                    p1=(p1.x, p1.y),
                    p2=(p2.x, p2.y),
                    cut_point=hit_point,
                    sliced_target=False,
                    new_bodies=[b1, b2],
                    bonus_score=200
                ))

        return results

    def _remove_body(self, body: pymunk.Body) -> None:
        """Safely detach and remove a body and all attached shapes/constraints."""
        for shape in list(body.shapes):
            self.space.remove(shape)
        for constraint in list(body.constraints):
            self.space.remove(constraint)
        self.space.remove(body)
