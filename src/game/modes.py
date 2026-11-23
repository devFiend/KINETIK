"""Game Mode state machines: Free Play sandbox and Target Rush arcade mode."""
from abc import ABC, abstractmethod
from enum import Enum, auto
import random
from typing import List, Optional, Tuple
import pymunk

from src.game.scoring import ScoringEngine
from src.physics.collisions import COLLISION_TYPE_PROP, COLLISION_TYPE_TARGET, CollisionEvent
from src.physics.targets import TargetDrone, TargetKind
from src.physics.world import PhysicsWorld


class ModeType(Enum):
    FREE_PLAY = "Free Play (Sandbox)"
    TARGET_RUSH = "Target Rush (60s Arcade)"
    THE_STACK = "The Stack (Zen Tower Balance)"


class GameModeState(Enum):
    PLAYING = auto()
    PAUSED = auto()
    ROUND_OVER = auto()


class BaseGameMode(ABC):
    """Abstract base for KINETIK game modes."""

    def __init__(self, mode_type: ModeType, physics_world: PhysicsWorld, scoring: ScoringEngine):
        self.mode_type = mode_type
        self.physics_world = physics_world
        self.scoring = scoring
        self.state = GameModeState.PLAYING

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass


class FreePlayMode(BaseGameMode):
    """Unlimited physics sandbox."""

    def __init__(self, physics_world: PhysicsWorld, scoring: ScoringEngine):
        super().__init__(ModeType.FREE_PLAY, physics_world, scoring)

    def start(self) -> None:
        self.state = GameModeState.PLAYING
        self.physics_world.reset_default_playground()

    def update(self, dt: float) -> None:
        pass  # Unrestricted freeform play

    def reset(self) -> None:
        self.physics_world.reset_default_playground()


class TargetRushMode(BaseGameMode):
    """60-second timed competitive arcade mode with moving drone targets."""

    def __init__(self, physics_world: PhysicsWorld, scoring: ScoringEngine, round_duration_sec: float = 60.0):
        super().__init__(ModeType.TARGET_RUSH, physics_world, scoring)
        self.round_duration = round_duration_sec
        self.time_remaining = round_duration_sec
        self.targets: List[TargetDrone] = []
        self._spawn_timer = 0.0
        self._setup_target_collision_handler()

    def _setup_target_collision_handler(self) -> None:
        """Handle thrown projectile impacts on target drones."""
        def on_target_hit(arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> None:
            if self.state != GameModeState.PLAYING:
                return

            # Retrieve target drone reference
            shape_a, shape_b = arbiter.shapes
            target_shape = shape_a if shape_a.collision_type == COLLISION_TYPE_TARGET else shape_b
            prop_shape = shape_b if target_shape is shape_a else shape_a

            target_body = target_shape.body
            target_drone: Optional[TargetDrone] = getattr(target_body, "target_ref", None)

            if target_drone and target_drone.alive:
                contact_pt = arbiter.contact_point_set.points[0].point_a if arbiter.contact_point_set.points else target_body.position
                speed = prop_shape.body.velocity.length

                # Register hit with scoring engine
                self.scoring.register_hit(
                    base_points=target_drone.base_points,
                    impact_speed=speed,
                    hit_pos=(contact_pt.x, contact_pt.y),
                    color=target_drone.color
                )

                # Bonus time for golden snitch
                if target_drone.kind == TargetKind.GOLDEN_SNITCH:
                    self.time_remaining = min(self.round_duration, self.time_remaining + 5.0)

                # Shatter target
                target_drone.destroy()

        self.physics_world.space.on_collision(
            COLLISION_TYPE_PROP,
            COLLISION_TYPE_TARGET,
            post_solve=on_target_hit
        )

    def start(self) -> None:
        self.state = GameModeState.PLAYING
        self.time_remaining = self.round_duration
        self.scoring.reset()
        self._clear_targets()
        self.physics_world.clear_dynamic_bodies()

        # Spawn a few initial bouncing spheres for throwing
        cx = self.physics_world.width * 0.5
        self.physics_world.spawn_sphere(cx - 100.0, 500.0, radius=28.0)
        self.physics_world.spawn_sphere(cx + 100.0, 500.0, radius=28.0)

        # Spawn initial targets
        self._spawn_target(TargetKind.STANDARD)
        self._spawn_target(TargetKind.SPEED_RUNNER)

    def _clear_targets(self) -> None:
        for t in list(self.targets):
            t.destroy()
        self.targets.clear()

    def _spawn_target(self, kind: TargetKind = TargetKind.STANDARD) -> None:
        """Spawn target drone at randomized upper-screen coordinates."""
        tx = random.uniform(180, self.physics_world.width - 180)
        ty = random.uniform(140, self.physics_world.height * 0.45)
        drone = TargetDrone(self.physics_world.space, tx, ty, kind=kind)
        self.targets.append(drone)

    def update(self, dt: float) -> None:
        if self.state != GameModeState.PLAYING:
            return

        # Advance round clock
        self.time_remaining -= dt
        if self.time_remaining <= 0.0:
            self.time_remaining = 0.0
            self.state = GameModeState.ROUND_OVER
            return

        # Update and purge dead targets
        self.targets = [t for t in self.targets if t.update(dt)]

        # Maintain active target count (between 2 and 4 targets)
        self._spawn_timer += dt
        if len(self.targets) < 3 and self._spawn_timer >= 1.5:
            self._spawn_timer = 0.0
            roll = random.random()
            if roll < 0.2:
                self._spawn_target(TargetKind.GOLDEN_SNITCH)
            elif roll < 0.6:
                self._spawn_target(TargetKind.SPEED_RUNNER)
            else:
                self._spawn_target(TargetKind.STANDARD)

        # Ensure player always has projectiles to throw
        if len(self.physics_world.get_dynamic_bodies()) < 2:
            self.physics_world.spawn_sphere(
                random.uniform(200, self.physics_world.width - 200),
                520.0,
                radius=random.uniform(24, 30)
            )

    def reset(self) -> None:
        self.start()
