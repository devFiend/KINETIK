"""Ragdoll multi-body physics composite: articulated joints, angular limits, and comedic facial state."""
from dataclasses import dataclass
from enum import Enum, auto
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
from src.physics.collisions import COLLISION_TYPE_PROP
from src.physics.objects import PropType, PropVisualData


class RagdollExpression(Enum):
    HAPPY = auto()
    PANIC_SCREAM = auto()
    GRABBED = auto()
    DIZZY = auto()
    KNOCKED_OUT = auto()


_ragdoll_counter = 1


class Ragdoll:
    """
    Articulated multi-body humanoid character with realistic skeletal constraints:
    - Head, Torso, Left/Right Arms (Upper + Forearm), Left/Right Legs (Thigh + Shin)
    - Pivot joints + RotaryLimit joints simulating anatomical limits
    - Self-collision masking via Pymunk ShapeFilter groups
    - Dynamic emotional facial state machine reacting to speed, grabs, and collisions
    """

    def __init__(self, space: pymunk.Space, x: float, y: float, scale: float = 1.0):
        global _ragdoll_counter
        self.space = space
        self.scale = scale
        self.group_id = _ragdoll_counter
        _ragdoll_counter += 1

        self.filter = pymunk.ShapeFilter(group=self.group_id)
        self.expression = RagdollExpression.HAPPY
        self.dizzy_timer = 0.0
        self.scream_timer = 0.0
        self.total_impacts = 0
        self.coins_earned = 0

        self.bodies: List[pymunk.Body] = []
        self.shapes: List[pymunk.Shape] = []
        self.joints: List[pymunk.Constraint] = []

        self._build_skeleton(x, y)

    def _build_skeleton(self, root_x: float, root_y: float) -> None:
        s = self.scale

        # --- 1. Torso ---
        torso_w, torso_h = 26.0 * s, 54.0 * s
        torso_mass = 3.5
        torso_moment = pymunk.moment_for_box(torso_mass, (torso_w, torso_h))
        self.torso = pymunk.Body(torso_mass, torso_moment, body_type=pymunk.Body.DYNAMIC)
        self.torso.position = pymunk.Vec2d(root_x, root_y)
        torso_shape = pymunk.Poly.create_box(self.torso, (torso_w, torso_h))
        torso_shape.elasticity = 0.5
        torso_shape.friction = 0.8
        torso_shape.filter = self.filter
        torso_shape.collision_type = COLLISION_TYPE_PROP
        self.torso.custom_data = PropVisualData(
            prop_type=PropType.BOX,
            primary_color=(60, 140, 240),
            glow_color=COLOR_CYAN_GLOW,
            width=torso_w,
            height=torso_h
        )
        self.space.add(self.torso, torso_shape)
        self.bodies.append(self.torso)
        self.shapes.append(torso_shape)

        # --- 2. Head ---
        head_r = 18.0 * s
        head_mass = 1.2
        head_moment = pymunk.moment_for_circle(head_mass, 0, head_r)
        self.head = pymunk.Body(head_mass, head_moment, body_type=pymunk.Body.DYNAMIC)
        self.head.position = pymunk.Vec2d(root_x, root_y - (torso_h * 0.5 + head_r + 2.0 * s))
        head_shape = pymunk.Circle(self.head, head_r)
        head_shape.elasticity = 0.7
        head_shape.friction = 0.6
        head_shape.filter = self.filter
        head_shape.collision_type = COLLISION_TYPE_PROP
        self.head.custom_data = PropVisualData(
            prop_type=PropType.SPHERE,
            primary_color=(255, 210, 160),
            glow_color=COLOR_GOLD_AMBER,
            radius=head_r
        )
        self.space.add(self.head, head_shape)
        self.bodies.append(self.head)
        self.shapes.append(head_shape)

        # Neck Joint
        neck_pivot = pymunk.PivotJoint(self.torso, self.head, (0.0, -torso_h * 0.5), (0.0, head_r))
        neck_limit = pymunk.RotaryLimitJoint(self.torso, self.head, -0.4, 0.4)
        self.space.add(neck_pivot, neck_limit)
        self.joints.extend([neck_pivot, neck_limit])

        # Helper to create limb segment capsule
        def make_limb(w: float, h: float, mass: float, px: float, py: float, color: Tuple[int, int, int]) -> Tuple[pymunk.Body, pymunk.Shape]:
            m = pymunk.moment_for_box(mass, (w, h))
            body = pymunk.Body(mass, m, body_type=pymunk.Body.DYNAMIC)
            body.position = pymunk.Vec2d(px, py)
            shape = pymunk.Poly.create_box(body, (w, h))
            shape.elasticity = 0.6
            shape.friction = 0.7
            shape.filter = self.filter
            shape.collision_type = COLLISION_TYPE_PROP
            body.custom_data = PropVisualData(
                prop_type=PropType.BOX,
                primary_color=color,
                glow_color=COLOR_CYAN_GLOW,
                width=w,
                height=h
            )
            self.space.add(body, shape)
            self.bodies.append(body)
            self.shapes.append(shape)
            return body, shape

        arm_w, arm_h = 10.0 * s, 24.0 * s
        leg_w, leg_h = 12.0 * s, 28.0 * s

        # --- 3. Left Arm (Upper + Forearm) ---
        lux = root_x - (torso_w * 0.5 + arm_w * 0.5)
        luy = root_y - torso_h * 0.3
        self.left_arm, _ = make_limb(arm_w, arm_h, 0.6, lux, luy, (80, 160, 255))
        self.left_forearm, _ = make_limb(arm_w * 0.9, arm_h * 0.9, 0.5, lux, luy + arm_h, (255, 210, 160))

        # Left Shoulder & Elbow
        l_sh = pymunk.PivotJoint(self.torso, self.left_arm, (-torso_w * 0.5, -torso_h * 0.35), (0.0, -arm_h * 0.45))
        l_sh_lim = pymunk.RotaryLimitJoint(self.torso, self.left_arm, -2.0, 2.0)
        l_elb = pymunk.PivotJoint(self.left_arm, self.left_forearm, (0.0, arm_h * 0.45), (0.0, -arm_h * 0.4))
        l_elb_lim = pymunk.RotaryLimitJoint(self.left_arm, self.left_forearm, -2.4, 0.1)
        self.space.add(l_sh, l_sh_lim, l_elb, l_elb_lim)
        self.joints.extend([l_sh, l_sh_lim, l_elb, l_elb_lim])

        # --- 4. Right Arm (Upper + Forearm) ---
        rux = root_x + (torso_w * 0.5 + arm_w * 0.5)
        ruy = root_y - torso_h * 0.3
        self.right_arm, _ = make_limb(arm_w, arm_h, 0.6, rux, ruy, (80, 160, 255))
        self.right_forearm, _ = make_limb(arm_w * 0.9, arm_h * 0.9, 0.5, rux, ruy + arm_h, (255, 210, 160))

        # Right Shoulder & Elbow
        r_sh = pymunk.PivotJoint(self.torso, self.right_arm, (torso_w * 0.5, -torso_h * 0.35), (0.0, -arm_h * 0.45))
        r_sh_lim = pymunk.RotaryLimitJoint(self.torso, self.right_arm, -2.0, 2.0)
        r_elb = pymunk.PivotJoint(self.right_arm, self.right_forearm, (0.0, arm_h * 0.45), (0.0, -arm_h * 0.4))
        r_elb_lim = pymunk.RotaryLimitJoint(self.right_arm, self.right_forearm, -0.1, 2.4)
        self.space.add(r_sh, r_sh_lim, r_elb, r_elb_lim)
        self.joints.extend([r_sh, r_sh_lim, r_elb, r_elb_lim])

        # --- 5. Left Leg (Thigh + Shin) ---
        llx = root_x - torso_w * 0.3
        lly = root_y + torso_h * 0.5 + leg_h * 0.5
        self.left_thigh, _ = make_limb(leg_w, leg_h, 0.9, llx, lly, (40, 80, 180))
        self.left_shin, _ = make_limb(leg_w * 0.9, leg_h * 0.9, 0.7, llx, lly + leg_h, (30, 30, 45))

        # Left Hip & Knee
        l_hip = pymunk.PivotJoint(self.torso, self.left_thigh, (-torso_w * 0.3, torso_h * 0.5), (0.0, -leg_h * 0.45))
        l_hip_lim = pymunk.RotaryLimitJoint(self.torso, self.left_thigh, -1.3, 1.3)
        l_knee = pymunk.PivotJoint(self.left_thigh, self.left_shin, (0.0, leg_h * 0.45), (0.0, -leg_h * 0.4))
        l_knee_lim = pymunk.RotaryLimitJoint(self.left_thigh, self.left_shin, 0.0, 2.4)
        self.space.add(l_hip, l_hip_lim, l_knee, l_knee_lim)
        self.joints.extend([l_hip, l_hip_lim, l_knee, l_knee_lim])

        # --- 6. Right Leg (Thigh + Shin) ---
        rlx = root_x + torso_w * 0.3
        rly = root_y + torso_h * 0.5 + leg_h * 0.5
        self.right_thigh, _ = make_limb(leg_w, leg_h, 0.9, rlx, rly, (40, 80, 180))
        self.right_shin, _ = make_limb(leg_w * 0.9, leg_h * 0.9, 0.7, rlx, rly + leg_h, (30, 30, 45))

        # Right Hip & Knee
        r_hip = pymunk.PivotJoint(self.torso, self.right_thigh, (torso_w * 0.3, torso_h * 0.5), (0.0, -leg_h * 0.45))
        r_hip_lim = pymunk.RotaryLimitJoint(self.torso, self.right_thigh, -1.3, 1.3)
        r_knee = pymunk.PivotJoint(self.right_thigh, self.right_shin, (0.0, leg_h * 0.45), (0.0, -leg_h * 0.4))
        r_knee_lim = pymunk.RotaryLimitJoint(self.right_thigh, self.right_shin, 0.0, 2.4)
        self.space.add(r_hip, r_hip_lim, r_knee, r_knee_lim)
        self.joints.extend([r_hip, r_hip_lim, r_knee, r_knee_lim])

        # Tag all bodies with ragdoll owner reference
        for b in self.bodies:
            b.ragdoll_owner = self

    @property
    def speed(self) -> float:
        """Root movement speed."""
        return self.torso.velocity.length

    @property
    def is_held(self) -> bool:
        """True if any body in this ragdoll is currently being held by telekinesis."""
        return any(
            getattr(b, "custom_data", None) and b.custom_data.is_held
            for b in self.bodies
        )

    def register_impact(self, impulse: float) -> int:
        """
        Record collision force on the ragdoll.
        Returns coins/points awarded for comedic punishment.
        """
        if impulse < 80.0:
            return 0

        self.total_impacts += 1
        coins = int(impulse * 0.25)
        self.coins_earned += coins

        if impulse > 400.0:
            self.dizzy_timer = 2.0
            self.expression = RagdollExpression.DIZZY
        elif impulse > 200.0:
            self.scream_timer = 0.8
            self.expression = RagdollExpression.PANIC_SCREAM

        return coins

    def update(self, dt: float) -> None:
        """Update emotional state machine based on speed, grabs, and timers."""
        if self.dizzy_timer > 0.0:
            self.dizzy_timer -= dt
            self.expression = RagdollExpression.DIZZY
            return

        if self.scream_timer > 0.0:
            self.scream_timer -= dt
            self.expression = RagdollExpression.PANIC_SCREAM
            return

        if self.is_held:
            self.expression = RagdollExpression.GRABBED
        elif self.speed > 550.0:
            self.expression = RagdollExpression.PANIC_SCREAM
        else:
            self.expression = RagdollExpression.HAPPY

    def destroy(self) -> None:
        """Cleanly remove all joints, shapes, and bodies from physics space."""
        for joint in list(self.joints):
            if joint in self.space.constraints:
                self.space.remove(joint)
        self.joints.clear()

        for shape in list(self.shapes):
            if shape in self.space.shapes:
                self.space.remove(shape)
        self.shapes.clear()

        for body in list(self.bodies):
            if body in self.space.bodies:
                self.space.remove(body)
        self.bodies.clear()
