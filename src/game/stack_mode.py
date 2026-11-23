"""The Stack: Zen Tower Balancing Physics Mode."""
from dataclasses import dataclass
import math
import random
from typing import List, Optional, Tuple
import pymunk

from src.config import (
    COLOR_CYAN_GLOW,
    COLOR_GOLD_AMBER,
    COLOR_HAZARD_RED,
    COLOR_VIOLET_FLUX,
    COLOR_WHITE_BRIGHT,
)
from src.game.modes import BaseGameMode, GameModeState, ModeType
from src.game.scoring import ScoringEngine
from src.physics.world import PhysicsWorld


CHECKPOINT_ALTITUDES = [160.0, 300.0, 440.0, 580.0, 700.0]
HOLD_DURATION_REQUIRED = 2.5  # Seconds of stability to clear tier


@dataclass
class StackCheckpointEvent:
    tier: int
    altitude: float
    bonus_points: int


class TheStackMode(BaseGameMode):
    """
    Zen Tower Balancing Physics Mode:
    Telekinetically lift, align, and balance geometry onto a rising tower.
    Hold tower height above altitude checkpoints in stable equilibrium to advance tiers.
    """

    def __init__(self, physics_world: PhysicsWorld, scoring: ScoringEngine):
        super().__init__(ModeType.THE_STACK, physics_world, scoring)
        self.current_tier: int = 1
        self.max_tier: int = len(CHECKPOINT_ALTITUDES)
        self.hold_timer: float = 0.0
        self.current_altitude: float = 0.0
        self.record_altitude: float = 0.0
        self.is_stable: bool = False
        self.recent_checkpoint_event: Optional[StackCheckpointEvent] = None
        self._event_timer: float = 0.0
        self._spawn_cooldown: float = 0.0

    @property
    def target_altitude(self) -> float:
        tier_idx = min(self.current_tier - 1, len(CHECKPOINT_ALTITUDES) - 1)
        return CHECKPOINT_ALTITUDES[tier_idx]

    @property
    def hold_progress(self) -> float:
        return min(1.0, self.hold_timer / HOLD_DURATION_REQUIRED)

    def start(self) -> None:
        self.state = GameModeState.PLAYING
        self.current_tier = 1
        self.hold_timer = 0.0
        self.current_altitude = 0.0
        self.record_altitude = 0.0
        self.is_stable = False
        self.recent_checkpoint_event = None
        self._spawn_cooldown = 0.0

        self.physics_world.clear_dynamic_bodies()
        floor_y = self.physics_world.height - 10.0
        cx = self.physics_world.width * 0.5

        # 1. Spawn wide heavy foundation base in center
        self.physics_world.spawn_plank(cx, floor_y - 25.0, width=220.0, height=36.0)

        # 2. Spawn initial staging blocks on left and right wings
        self._replenish_staging()

    def _replenish_staging(self) -> None:
        """Spawn blocks and planks in the left and right staging zones."""
        floor_y = self.physics_world.height - 10.0
        left_x = 180.0
        right_x = self.physics_world.width - 180.0

        dynamic_bodies = self.physics_world.get_dynamic_bodies()

        # Count how many bodies are in left staging vs right staging
        left_count = sum(1 for b in dynamic_bodies if b.position.x < 300.0)
        right_count = sum(1 for b in dynamic_bodies if b.position.x > self.physics_world.width - 300.0)

        if left_count < 2:
            roll = random.random()
            if roll < 0.5:
                self.physics_world.spawn_box(left_x, floor_y - 120.0, size=random.uniform(44.0, 56.0))
            else:
                self.physics_world.spawn_plank(left_x, floor_y - 120.0, width=130.0, height=24.0)

        if right_count < 2:
            roll = random.random()
            if roll < 0.5:
                self.physics_world.spawn_box(right_x, floor_y - 120.0, size=random.uniform(44.0, 56.0))
            else:
                self.physics_world.spawn_plank(right_x, floor_y - 120.0, width=130.0, height=24.0)

    def _measure_tower(self) -> Tuple[float, bool]:
        """
        Calculate current tower altitude and stability in the central construction zone.
        Returns (highest_altitude_px, is_stable).
        """
        floor_y = self.physics_world.height - 10.0
        cx = self.physics_world.width * 0.5
        zone_min_x = cx - 240.0
        zone_max_x = cx + 240.0

        tower_bodies = []
        highest_point_y = floor_y

        for body in self.physics_world.get_dynamic_bodies():
            bx = body.position.x
            by = body.position.y
            if zone_min_x <= bx <= zone_max_x and by <= floor_y:
                tower_bodies.append(body)
                # Compute highest visual point across all shapes (in screen coordinates, min y is top)
                for shape in body.shapes:
                    bb = shape.bb
                    if bb.bottom < highest_point_y:
                        highest_point_y = bb.bottom

        altitude = max(0.0, floor_y - highest_point_y)

        # Stability evaluation: check velocities of tower bodies
        if not tower_bodies:
            return 0.0, False

        max_speed = max(b.velocity.length for b in tower_bodies)
        # Stable if props are at rest / near equilibrium (< 45 px/s)
        stable = (max_speed < 45.0)

        return altitude, stable

    def update(self, dt: float) -> None:
        if self.state != GameModeState.PLAYING:
            return

        self._spawn_cooldown += dt
        if self._spawn_cooldown >= 3.0:
            self._spawn_cooldown = 0.0
            self._replenish_staging()

        # Update event timer
        if self.recent_checkpoint_event:
            self._event_timer += dt
            if self._event_timer > 3.0:
                self.recent_checkpoint_event = None
                self._event_timer = 0.0

        # Measure stack geometry
        alt, stable = self._measure_tower()
        self.current_altitude = alt
        self.is_stable = stable
        if alt > self.record_altitude:
            self.record_altitude = alt

        target = self.target_altitude

        # Hold progress check
        if alt >= target and stable:
            self.hold_timer += dt
            if self.hold_timer >= HOLD_DURATION_REQUIRED:
                # Checkpoint reached!
                bonus = self.current_tier * 500
                cx = self.physics_world.width * 0.5
                checkpoint_y = (self.physics_world.height - 10.0) - target

                self.scoring.register_hit(
                    base_points=bonus,
                    impact_speed=1000.0,
                    hit_pos=(cx, checkpoint_y),
                    color=COLOR_GOLD_AMBER
                )

                self.recent_checkpoint_event = StackCheckpointEvent(
                    tier=self.current_tier,
                    altitude=alt,
                    bonus_points=bonus
                )
                self._event_timer = 0.0

                if self.current_tier < self.max_tier:
                    self.current_tier += 1
                    self.hold_timer = 0.0
                else:
                    # Max tier cleared!
                    self.hold_timer = HOLD_DURATION_REQUIRED
        else:
            # Decay hold timer if unstable or below altitude
            self.hold_timer = max(0.0, self.hold_timer - dt * 1.5)

    def reset(self) -> None:
        self.start()
