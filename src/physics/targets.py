"""Interactive Target Drone obstacles for Target Rush arcade mode."""
from enum import Enum, auto
import math
import random
from typing import Optional, Tuple
import pymunk

from src.config import (
    COLOR_CYAN_GLOW,
    COLOR_GOLD_AMBER,
    COLOR_HAZARD_RED,
    COLOR_VIOLET_FLUX,
    COLOR_WHITE_BRIGHT,
)
from src.physics.collisions import COLLISION_TYPE_TARGET


class TargetKind(Enum):
    """Target drone classification."""
    STANDARD = auto()
    SPEED_RUNNER = auto()
    GOLDEN_SNITCH = auto()


class TargetDrone:
    """A floating kinematic target drone that can be struck by thrown objects."""

    def __init__(
        self,
        space: pymunk.Space,
        x: float,
        y: float,
        kind: TargetKind = TargetKind.STANDARD
    ):
        self.space = space
        self.base_x = x
        self.base_y = y
        self.kind = kind
        self.alive = True
        self.time_alive = 0.0

        if kind == TargetKind.GOLDEN_SNITCH:
            self.radius = 18.0
            self.base_points = 1000
            self.color = COLOR_GOLD_AMBER
            self.time_limit = 5.0  # Disappears after 5s
        elif kind == TargetKind.SPEED_RUNNER:
            self.radius = 24.0
            self.base_points = 250
            self.color = COLOR_VIOLET_FLUX
            self.time_limit = 0.0
        else:
            self.radius = 28.0
            self.base_points = 100
            self.color = COLOR_CYAN_GLOW
            self.time_limit = 0.0

        # Create Kinematic body so targets hover in place
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = pymunk.Vec2d(x, y)

        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.collision_type = COLLISION_TYPE_TARGET
        self.shape.sensor = False  # Solid obstacle to bounce projectiles

        # Associate this target object with the Pymunk body
        self.body.target_ref = self
        self.space.add(self.body, self.shape)

    def update(self, dt: float) -> bool:
        """Update drift trajectory. Returns False if target expired naturally."""
        if not self.alive:
            return False

        self.time_alive += dt
        if self.time_limit > 0.0 and self.time_alive >= self.time_limit:
            self.destroy()
            return False

        # Oscillating drift movement pattern
        if self.kind == TargetKind.SPEED_RUNNER:
            new_x = self.base_x + math.sin(self.time_alive * 3.5) * 120.0
            new_y = self.base_y + math.cos(self.time_alive * 2.5) * 60.0
        elif self.kind == TargetKind.GOLDEN_SNITCH:
            new_x = self.base_x + math.sin(self.time_alive * 5.0) * 160.0
            new_y = self.base_y + math.sin(self.time_alive * 7.0) * 80.0
        else:
            new_x = self.base_x + math.sin(self.time_alive * 1.5) * 40.0
            new_y = self.base_y + math.cos(self.time_alive * 1.2) * 25.0

        self.body.position = pymunk.Vec2d(new_x, new_y)
        return True

    def destroy(self) -> None:
        """Remove target from physics space cleanly."""
        if self.alive:
            self.alive = False
            if self.shape in self.space.shapes:
                self.space.remove(self.shape)
            if self.body in self.space.bodies:
                self.space.remove(self.body)
