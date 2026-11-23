"""Kinetic energy shield forcefield deflecting projectiles and hazards."""
import math
from typing import Optional, Tuple
import pygame
import pymunk

from src.config import COLOR_CYAN_GLOW, COLOR_WHITE_BRIGHT
from src.physics.collisions import COLLISION_TYPE_WALL


class KineticShield:
    """
    Kinematic hexagonal forcefield deflector attached to an open, flat non-dominant hand.
    Reflects projectiles with energetic restitution (bouncy elastic deflection).
    """

    def __init__(self, space: pymunk.Space, radius: float = 65.0):
        self.space = space
        self.radius = radius
        self.active = False
        self.position = (0.0, 0.0)
        self.angle = 0.0

        # Kinematic body for the shield
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = pymunk.Vec2d(-1000.0, -1000.0)

        # Deflection segment
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.elasticity = 1.35  # Super-elastic energy bounce
        self.shape.friction = 0.2
        self.shape.collision_type = COLLISION_TYPE_WALL

    def activate(self, pos: Tuple[float, float]) -> None:
        """Activate shield at hand coordinates."""
        self.position = pos
        self.body.position = pymunk.Vec2d(pos[0], pos[1])
        if not self.active:
            self.active = True
            if self.body not in self.space.bodies:
                self.space.add(self.body, self.shape)

    def update_position(self, pos: Tuple[float, float]) -> None:
        """Move active shield to updated hand position."""
        if self.active:
            self.position = pos
            self.body.position = pymunk.Vec2d(pos[0], pos[1])

    def deactivate(self) -> None:
        """Deactivate and remove shield from physics simulation."""
        if self.active:
            self.active = False
            if self.shape in self.space.shapes:
                self.space.remove(self.shape)
            if self.body in self.space.bodies:
                self.space.remove(self.body)

    def draw(self, surface: pygame.Surface) -> None:
        """Render glowing hexagonal forcefield with pulsing nodes."""
        if not self.active:
            return

        cx, cy = int(self.position[0]), int(self.position[1])
        r = int(self.radius)

        # Draw hexagon
        points = []
        for i in range(6):
            a = i * (math.pi / 3.0)
            px = int(cx + math.cos(a) * r)
            py = int(cy + math.sin(a) * r)
            points.append((px, py))

        # Outer forcefield line
        pygame.draw.polygon(surface, COLOR_CYAN_GLOW, points, 3)
        # Inner shield core
        pygame.draw.polygon(surface, (20, 180, 255), points, 1)

        # Corner nodes
        for px, py in points:
            pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, (px, py), 3)

        # Center core reticle
        pygame.draw.circle(surface, COLOR_CYAN_GLOW, (cx, cy), 8, 2)
