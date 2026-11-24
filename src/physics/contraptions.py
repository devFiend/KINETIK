"""Interactive playground contraptions: Pinball Bumpers, Wormhole Portals, Trampolines, and TNT Barrels."""
from dataclasses import dataclass
import math
import random
import time
from typing import Dict, List, Optional, Tuple
import pymunk

from src.config import (
    COLOR_CYAN_GLOW,
    COLOR_GOLD_AMBER,
    COLOR_HAZARD_RED,
    COLOR_VIOLET_FLUX,
    COLOR_WHITE_BRIGHT,
)
from src.physics.collisions import COLLISION_TYPE_PROP, COLLISION_TYPE_WALL


COLLISION_TYPE_BUMPER = 5
COLLISION_TYPE_TRAMPOLINE = 6


class PinballBumper:
    """
    Circular neon pinball bumper that imparts high-energy elastic repulsive shockwaves
    when struck by ragdoll limbs or physical props.
    """

    def __init__(self, space: pymunk.Space, x: float, y: float, radius: float = 46.0, bounce_impulse: float = 1400.0):
        self.space = space
        self.x = x
        self.y = y
        self.radius = radius
        self.bounce_impulse = bounce_impulse
        self.flash_timer: float = 0.0
        self.hit_count: int = 0

        # Kinematic body so bumper remains rigidly fixed in space
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = pymunk.Vec2d(x, y)

        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.elasticity = 1.6
        self.shape.friction = 0.2
        self.shape.collision_type = COLLISION_TYPE_BUMPER
        self.shape.bumper_ref = self

        self.space.add(self.body, self.shape)

    def trigger_hit(self, hit_body: pymunk.Body) -> Tuple[float, float]:
        """Repel colliding body outward from bumper center with explosive impulse."""
        self.flash_timer = 0.25
        self.hit_count += 1

        dx = hit_body.position.x - self.x
        dy = hit_body.position.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 1e-3:
            nx = dx / dist
            ny = dy / dist
        else:
            nx, ny = 0.0, -1.0

        hit_body.velocity = pymunk.Vec2d(nx * self.bounce_impulse, ny * self.bounce_impulse)
        return (self.x + nx * self.radius, self.y + ny * self.radius)

    def update(self, dt: float) -> None:
        if self.flash_timer > 0.0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

    def destroy(self) -> None:
        if self.shape in self.space.shapes:
            self.space.remove(self.shape)
        if self.body in self.space.bodies:
            self.space.remove(self.body)


class PortalPair:
    """
    Coupled Wormhole Portals:
    Objects entering Portal A emerge from Portal B with preserved momentum, and vice-versa.
    """

    def __init__(self, pos_a: Tuple[float, float], pos_b: Tuple[float, float], radius: float = 40.0):
        self.pos_a = pos_a
        self.pos_b = pos_b
        self.radius = radius
        self.cooldowns: Dict[pymunk.Body, float] = {}

    def update_and_teleport(self, bodies: List[pymunk.Body], dt: float, now: float) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Check all dynamic bodies for portal proximity and teleport them across dimensions.
        Returns list of (source_pos, target_pos) for portal jump VFX.
        """
        # Clean expired cooldowns
        for b in list(self.cooldowns.keys()):
            if now - self.cooldowns[b] > 0.6:
                del self.cooldowns[b]

        jumps = []
        for body in bodies:
            if body in self.cooldowns:
                continue

            bx, by = body.position.x, body.position.y

            # Check Portal A -> Portal B
            dist_a = math.hypot(bx - self.pos_a[0], by - self.pos_a[1])
            if dist_a < self.radius:
                self.cooldowns[body] = now
                body.position = pymunk.Vec2d(self.pos_b[0], self.pos_b[1])
                # Invert or deflect velocity slightly so it shoots cleanly out
                body.velocity = pymunk.Vec2d(body.velocity.x * 1.15, -abs(body.velocity.y) * 1.15)
                jumps.append((self.pos_a, self.pos_b))
                continue

            # Check Portal B -> Portal A
            dist_b = math.hypot(bx - self.pos_b[0], by - self.pos_b[1])
            if dist_b < self.radius:
                self.cooldowns[body] = now
                body.position = pymunk.Vec2d(self.pos_a[0], self.pos_a[1])
                body.velocity = pymunk.Vec2d(body.velocity.x * 1.15, -abs(body.velocity.y) * 1.15)
                jumps.append((self.pos_b, self.pos_a))

        return jumps


class Trampoline:
    """
    High-restitution floor launcher pad that propels bodies into stratospheric heights.
    """

    def __init__(self, space: pymunk.Space, x: float, y: float, width: float = 160.0):
        self.space = space
        self.x = x
        self.y = y
        self.width = width
        self.bounce_timer: float = 0.0

        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = pymunk.Vec2d(x, y)

        half_w = width * 0.5
        self.shape = pymunk.Segment(self.body, (-half_w, 0.0), (half_w, 0.0), 12.0)
        self.shape.elasticity = 2.0  # Ultra springy
        self.shape.friction = 0.4
        self.shape.collision_type = COLLISION_TYPE_TRAMPOLINE
        self.shape.trampoline_ref = self

        self.space.add(self.body, self.shape)

    def trigger_bounce(self, hit_body: pymunk.Body) -> None:
        self.bounce_timer = 0.2
        # Launch forcefully upwards
        hit_body.velocity = pymunk.Vec2d(hit_body.velocity.x * 0.8, -1350.0)

    def update(self, dt: float) -> None:
        if self.bounce_timer > 0.0:
            self.bounce_timer = max(0.0, self.bounce_timer - dt)

    def destroy(self) -> None:
        if self.shape in self.space.shapes:
            self.space.remove(self.shape)
        if self.body in self.space.bodies:
            self.space.remove(self.body)
