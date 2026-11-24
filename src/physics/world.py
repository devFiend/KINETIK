"""Pymunk 2D rigid-body simulation world, boundary walls, and fixed timestep stepper."""
from typing import List, Optional, Tuple
import pymunk

from src.config import DEFAULT_GRAVITY_Y, FIXED_PHYSICS_DT
from src.physics.collisions import COLLISION_TYPE_WALL, CollisionDispatcher
from src.physics.objects import ObjectFactory


class PhysicsWorld:
    """
    Encapsulates the Pymunk 2D simulation space, static boundary segments,
    collision dispatching, and deterministic sub-stepping.
    """

    def __init__(
        self,
        width: int,
        height: int,
        gravity_y: float = DEFAULT_GRAVITY_Y,
        fixed_dt: float = FIXED_PHYSICS_DT
    ):
        self.width = width
        self.height = height
        self.gravity_y = gravity_y
        self.fixed_dt = fixed_dt
        self._accumulator = 0.0

        self.space = pymunk.Space()
        self.space.gravity = pymunk.Vec2d(0.0, self.gravity_y)
        self.space.damping = 0.99  # Gentle air resistance

        self.collision_dispatcher = CollisionDispatcher(self.space)
        self._boundary_shapes: List[pymunk.Segment] = []

        self._build_boundaries()

    @property
    def gravity(self) -> float:
        return self.space.gravity.y

    @gravity.setter
    def gravity(self, value: float) -> None:
        self.space.gravity = pymunk.Vec2d(0.0, value)

    def toggle_zero_gravity(self) -> bool:
        """Toggle between standard gravity and zero-gravity float mode."""
        if abs(self.space.gravity.y) > 1e-3:
            self.space.gravity = pymunk.Vec2d(0.0, 0.0)
            return True
        else:
            self.space.gravity = pymunk.Vec2d(0.0, self.gravity_y)
            return False

    def _build_boundaries(self) -> None:
        """Create static collision walls bounding the screen rectangle."""
        static_body = self.space.static_body
        thickness = 10.0
        elasticity = 0.7
        friction = 0.8

        corners = [
            (0.0, 0.0),                           # Top-Left
            (float(self.width), 0.0),             # Top-Right
            (float(self.width), float(self.height)),  # Bottom-Right
            (0.0, float(self.height))             # Bottom-Left
        ]

        # 4 Wall segments: Top, Right, Bottom (Floor), Left
        walls = [
            (corners[0], corners[1]),
            (corners[1], corners[2]),
            (corners[2], corners[3]),
            (corners[3], corners[0]),
        ]

        for p1, p2 in walls:
            seg = pymunk.Segment(static_body, p1, p2, thickness)
            seg.elasticity = elasticity
            seg.friction = friction
            seg.collision_type = COLLISION_TYPE_WALL
            self.space.add(seg)
            self._boundary_shapes.append(seg)

    def step(self, dt: float) -> int:
        """
        Advance simulation with fixed timestep accumulator.
        Returns the number of sub-steps executed.
        """
        self._accumulator += dt
        steps = 0
        # Prevent spiral of death on long frame delays
        if self._accumulator > 0.2:
            self._accumulator = 0.2

        while self._accumulator >= self.fixed_dt:
            self.space.step(self.fixed_dt)
            self._accumulator -= self.fixed_dt
            steps += 1

        return steps

    def get_dynamic_bodies(self) -> List[pymunk.Body]:
        """Return all active non-static bodies in the world."""
        return [b for b in self.space.bodies if b.body_type == pymunk.Body.DYNAMIC]

    def spawn_sphere(self, x: float, y: float, radius: float = 28.0) -> pymunk.Body:
        """Convenience spawner for a kinetic sphere."""
        return ObjectFactory.create_sphere(self.space, x, y, radius=radius)

    def spawn_box(self, x: float, y: float, size: float = 50.0) -> pymunk.Body:
        """Convenience spawner for a kinetic box."""
        return ObjectFactory.create_box(self.space, x, y, width=size, height=size)

    def spawn_plank(self, x: float, y: float, width: float = 120.0, height: float = 24.0) -> pymunk.Body:
        """Convenience spawner for a kinetic balancing plank."""
        return ObjectFactory.create_box(self.space, x, y, width=width, height=height, mass=2.5, friction=0.9)

    def clear_dynamic_bodies(self) -> None:
        """Remove all dynamic bodies and their attached shapes/constraints."""
        for body in list(self.space.bodies):
            if body.body_type == pymunk.Body.DYNAMIC:
                for constraint in list(body.constraints):
                    if constraint in self.space.constraints:
                        try:
                            self.space.remove(constraint)
                        except Exception:
                            pass
                for shape in list(body.shapes):
                    if shape in self.space.shapes:
                        try:
                            self.space.remove(shape)
                        except Exception:
                            pass
                if body in self.space.bodies:
                    try:
                        self.space.remove(body)
                    except Exception:
                        pass

    def reset_default_playground(self) -> None:
        """Clear dynamic objects and spawn a balanced starter set of physics props."""
        self.clear_dynamic_bodies()
        self.space.gravity = pymunk.Vec2d(0.0, self.gravity_y)

        cx = self.width * 0.5
        cy = self.height * 0.35

        # Starter set: 3 spheres and 2 boxes
        self.spawn_sphere(cx - 150.0, cy, radius=32.0)
        self.spawn_sphere(cx, cy - 80.0, radius=24.0)
        self.spawn_sphere(cx + 150.0, cy, radius=28.0)
        self.spawn_box(cx - 70.0, cy + 80.0, size=52.0)
        self.spawn_box(cx + 70.0, cy + 80.0, size=46.0)
