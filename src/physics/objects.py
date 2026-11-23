"""Physics object factories for dynamic spheres, crates, and target obstacles."""
from dataclasses import dataclass
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
from src.physics.collisions import COLLISION_TYPE_PROP


class PropType(Enum):
    """Type of interactive physics entity."""
    SPHERE = auto()
    BOX = auto()
    TARGET = auto()


@dataclass
class PropVisualData:
    """Cosmetic and presentation attributes for rendering physics bodies."""
    prop_type: PropType
    primary_color: Tuple[int, int, int]
    glow_color: Tuple[int, int, int]
    radius: float = 0.0
    width: float = 0.0
    height: float = 0.0
    is_held: bool = False
    is_target: bool = False


class ObjectFactory:
    """Factory helper to construct Pymunk rigid bodies and shapes with visual metadata."""

    @staticmethod
    def create_sphere(
        space: pymunk.Space,
        x: float,
        y: float,
        radius: float = 28.0,
        mass: float = 1.0,
        elasticity: float = 0.75,
        friction: float = 0.6,
        primary_color: Tuple[int, int, int] = COLOR_CYAN_GLOW
    ) -> pymunk.Body:
        """Create a dynamic bouncing sphere."""
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment, body_type=pymunk.Body.DYNAMIC)
        body.position = pymunk.Vec2d(x, y)

        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = COLLISION_TYPE_PROP

        # Attach visual metadata to the Pymunk body
        body.custom_data = PropVisualData(
            prop_type=PropType.SPHERE,
            primary_color=primary_color,
            glow_color=COLOR_WHITE_BRIGHT,
            radius=radius
        )

        space.add(body, shape)
        return body

    @staticmethod
    def create_box(
        space: pymunk.Space,
        x: float,
        y: float,
        width: float = 50.0,
        height: float = 50.0,
        mass: float = 2.0,
        elasticity: float = 0.4,
        friction: float = 0.8,
        primary_color: Tuple[int, int, int] = COLOR_VIOLET_FLUX
    ) -> pymunk.Body:
        """Create a dynamic rigid box/crate."""
        moment = pymunk.moment_for_box(mass, (width, height))
        body = pymunk.Body(mass, moment, body_type=pymunk.Body.DYNAMIC)
        body.position = pymunk.Vec2d(x, y)

        shape = pymunk.Poly.create_box(body, (width, height))
        shape.elasticity = elasticity
        shape.friction = friction
        shape.collision_type = COLLISION_TYPE_PROP

        body.custom_data = PropVisualData(
            prop_type=PropType.BOX,
            primary_color=primary_color,
            glow_color=COLOR_GOLD_AMBER,
            width=width,
            height=height
        )

        space.add(body, shape)
        return body
