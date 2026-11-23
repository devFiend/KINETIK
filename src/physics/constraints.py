"""Pymunk kinematic anchor body and soft damped spring constraint joints."""
from typing import Optional, Tuple
import pymunk

from src.config import SPRING_DAMPING, SPRING_STIFFNESS


class TelekineticJoint:
    """
    Connects a dynamic rigid body to a kinematic hand anchor using a soft Pymunk DampedSpring.
    Gives the object natural lag, momentum, and tactile mass feel rather than rigid snapping.
    """

    def __init__(
        self,
        space: pymunk.Space,
        target_body: pymunk.Body,
        initial_hand_pos: Tuple[float, float],
        stiffness: float = SPRING_STIFFNESS,
        damping: float = SPRING_DAMPING
    ):
        self.space = space
        self.target_body = target_body
        self.stiffness = stiffness
        self.damping = damping

        # Kinematic anchor body represents the telekinetic hand focal point
        self.hand_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.hand_body.position = pymunk.Vec2d(initial_hand_pos[0], initial_hand_pos[1])
        self.space.add(self.hand_body)

        # Connect hand anchor to target body center-of-mass (rest_length = 0)
        self.spring = pymunk.DampedSpring(
            self.hand_body,
            self.target_body,
            anchor_a=(0.0, 0.0),
            anchor_b=(0.0, 0.0),
            rest_length=0.0,
            stiffness=self.stiffness,
            damping=self.damping
        )
        self.space.add(self.spring)

        # Flag target body visual data as held
        if hasattr(self.target_body, "custom_data") and self.target_body.custom_data:
            self.target_body.custom_data.is_held = True

    def update_hand_position(self, pos: Tuple[float, float]) -> None:
        """Move the kinematic anchor body to the latest smoothed hand coordinates."""
        self.hand_body.position = pymunk.Vec2d(pos[0], pos[1])

    def detach(self) -> None:
        """Cleanly remove spring constraint and kinematic anchor from the physics space."""
        if hasattr(self.target_body, "custom_data") and self.target_body.custom_data:
            self.target_body.custom_data.is_held = False

        if self.spring in self.space.constraints:
            self.space.remove(self.spring)
        if self.hand_body in self.space.bodies:
            self.space.remove(self.hand_body)
