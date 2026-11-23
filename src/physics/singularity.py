"""Gravitational singularity attractor vortex (Black Hole rift)."""
import math
import random
from typing import List, Tuple
import pygame
import pymunk

from src.config import COLOR_VIOLET_FLUX, COLOR_WHITE_BRIGHT


class SingularityVortex:
    """
    A temporary gravitational black hole rift that draws in all surrounding physics props
    and target drones before collapsing into an energetic outward burst.
    """

    def __init__(
        self,
        space: pymunk.Space,
        center: Tuple[float, float],
        duration: float = 3.5,
        pull_radius: float = 420.0,
        pull_force: float = 2400.0
    ):
        self.space = space
        self.center = center
        self.duration = duration
        self.time_alive = 0.0
        self.pull_radius = pull_radius
        self.pull_force = pull_force
        self.active = True
        self.collapse_triggered = False

    def update(self, dt: float, dynamic_bodies: List[pymunk.Body]) -> bool:
        """Apply radial gravitational suction to all dynamic bodies in the arena."""
        if not self.active:
            return False

        self.time_alive += dt
        if self.time_alive >= self.duration:
            self.active = False
            return False

        cx, cy = self.center

        # Pull dynamic bodies towards singularity center
        for body in dynamic_bodies:
            bx, by = body.position.x, body.position.y
            dx = cx - bx
            dy = cy - by
            dist = math.hypot(dx, dy)

            if 20.0 < dist <= self.pull_radius:
                # Inverse-distance gravitational acceleration with vortex swirl
                pull_factor = (1.0 - dist / self.pull_radius) * (self.pull_force / dist)
                nx, ny = dx / dist, dy / dist

                # Tangential vortex velocity (swirl force)
                tx, ty = -ny * 0.4, nx * 0.4

                fx = (nx + tx) * pull_factor * body.mass * dt * 60.0
                fy = (ny + ty) * pull_factor * body.mass * dt * 60.0
                body.apply_impulse_at_world_point(pymunk.Vec2d(fx, fy), body.position)

        return True

    def draw(self, surface: pygame.Surface) -> None:
        """Render animated swirling accretion disk and black hole core."""
        if not self.active:
            return

        cx, cy = int(self.center[0]), int(self.center[1])
        t = self.time_alive

        # Outer gravitational distortion ring
        radius = int(45.0 + math.sin(t * 8.0) * 8.0)
        pygame.draw.circle(surface, COLOR_VIOLET_FLUX, (cx, cy), radius, 3)

        # Swirling accretion spirals
        for i in range(12):
            angle = t * 6.0 + i * (math.pi / 6.0)
            arm_r = radius * 0.8
            sx = int(cx + math.cos(angle) * arm_r)
            sy = int(cy + math.sin(angle) * arm_r)
            pygame.draw.circle(surface, (200, 100, 255), (sx, sy), 3)

        # Deep black core
        pygame.draw.circle(surface, (0, 0, 0), (cx, cy), 18)
        # Hot event horizon ring
        pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, (cx, cy), 19, 2)
