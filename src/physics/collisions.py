"""Collision categories, masks, and impact handler callbacks."""
from typing import Callable, List, Optional
import pymunk

# Collision Type IDs for Pymunk collision arbiters
COLLISION_TYPE_WALL = 1
COLLISION_TYPE_PROP = 2
COLLISION_TYPE_TARGET = 3
COLLISION_TYPE_HAND = 4


class CollisionEvent:
    """Carries telemetry about physical impacts in the simulation."""

    def __init__(
        self,
        type_a: int,
        type_b: int,
        impulse: float,
        contact_point: pymunk.Vec2d,
        body_a: pymunk.Body,
        body_b: pymunk.Body
    ):
        self.type_a = type_a
        self.type_b = type_b
        self.impulse = impulse
        self.contact_point = contact_point
        self.body_a = body_a
        self.body_b = body_b


class CollisionDispatcher:
    """Manages collision handlers and dispatches collision events to listeners."""

    def __init__(self, space: pymunk.Space):
        self.space = space
        self._listeners: List[Callable[[CollisionEvent], None]] = []
        self._setup_handlers()

    def add_listener(self, listener: Callable[[CollisionEvent], None]) -> None:
        """Register a callback for impact events."""
        self._listeners.append(listener)

    def _setup_handlers(self) -> None:
        """Configure Pymunk 7+ on_collision post-solve callbacks to measure impact energy."""
        # Prop <-> Wall impacts
        self.space.on_collision(
            COLLISION_TYPE_PROP,
            COLLISION_TYPE_WALL,
            post_solve=self._on_prop_wall_impact
        )

        # Prop <-> Prop impacts
        self.space.on_collision(
            COLLISION_TYPE_PROP,
            COLLISION_TYPE_PROP,
            post_solve=self._on_prop_prop_impact
        )

    def _on_prop_wall_impact(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> None:
        impulse = arbiter.total_impulse.length
        if impulse > 50.0 and arbiter.contact_point_set.points:
            pt = arbiter.contact_point_set.points[0].point_a
            event = CollisionEvent(
                type_a=COLLISION_TYPE_PROP,
                type_b=COLLISION_TYPE_WALL,
                impulse=impulse,
                contact_point=pt,
                body_a=arbiter.shapes[0].body,
                body_b=arbiter.shapes[1].body
            )
            for listener in self._listeners:
                listener(event)

    def _on_prop_prop_impact(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> None:
        impulse = arbiter.total_impulse.length
        if impulse > 50.0 and arbiter.contact_point_set.points:
            pt = arbiter.contact_point_set.points[0].point_a
            event = CollisionEvent(
                type_a=COLLISION_TYPE_PROP,
                type_b=COLLISION_TYPE_PROP,
                impulse=impulse,
                contact_point=pt,
                body_a=arbiter.shapes[0].body,
                body_b=arbiter.shapes[1].body
            )
            for listener in self._listeners:
                listener(event)
