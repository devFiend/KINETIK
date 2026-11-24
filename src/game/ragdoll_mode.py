"""Ragdoll God: Interactive Ragdoll Physics Playground game mode."""
from dataclasses import dataclass
import math
import random
import time
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
from src.physics.collisions import COLLISION_TYPE_PROP, COLLISION_TYPE_WALL
from src.physics.contraptions import (
    COLLISION_TYPE_BUMPER,
    COLLISION_TYPE_TRAMPOLINE,
    PinballBumper,
    PortalPair,
    Trampoline,
)
from src.physics.ragdoll import Ragdoll, RagdollExpression
from src.physics.world import PhysicsWorld


@dataclass
class TrickEvent:
    name: str
    points: int
    color: Tuple[int, int, int]
    timestamp: float


class RagdollGodMode(BaseGameMode):
    """
    Ragdoll God Mode:
    Fling, swing by limbs, juggle, and launch an articulated ragdoll into pinball bumpers,
    wormhole portals, and floor trampolines for hilarious physics slapstick and coin bonuses!
    """

    def __init__(self, physics_world: PhysicsWorld, scoring: ScoringEngine):
        super().__init__(ModeType.RAGDOLL_GOD, physics_world, scoring)
        self.ragdoll: Optional[Ragdoll] = None
        self.bumpers: List[PinballBumper] = []
        self.portals: Optional[PortalPair] = None
        self.trampoline: Optional[Trampoline] = None

        self.coins: int = 0
        self.combo: float = 1.0
        self.combo_timer: float = 0.0
        self.recent_trick: Optional[TrickEvent] = None
        self._scream_cooldown: float = 0.0
        self._setup_collision_handlers()

    def _setup_collision_handlers(self) -> None:
        """Handle interactions with pinball bumpers and trampolines."""
        # 1. Bumper Impact Handler
        def on_bumper_hit(arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> None:
            if self.state != GameModeState.PLAYING:
                return

            shape_a, shape_b = arbiter.shapes
            bumper_shape = shape_a if shape_a.collision_type == COLLISION_TYPE_BUMPER else shape_b
            prop_shape = shape_b if bumper_shape is shape_a else shape_a

            bumper: Optional[PinballBumper] = getattr(bumper_shape, "bumper_ref", None)
            if bumper:
                contact_pt = bumper.trigger_hit(prop_shape.body)
                pts = int(150 * self.combo)
                self.coins += pts
                self.scoring.register_hit(pts, 1200.0, contact_pt, COLOR_GOLD_AMBER)
                self._record_trick("PINBALL BUMPER!", pts, COLOR_GOLD_AMBER)
                self.combo = min(10.0, self.combo + 0.5)
                self.combo_timer = 2.5

        self.physics_world.space.on_collision(
            COLLISION_TYPE_PROP,
            COLLISION_TYPE_BUMPER,
            post_solve=on_bumper_hit
        )

        # 2. Trampoline Impact Handler
        def on_trampoline_hit(arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> None:
            if self.state != GameModeState.PLAYING:
                return

            shape_a, shape_b = arbiter.shapes
            tramp_shape = shape_a if shape_a.collision_type == COLLISION_TYPE_TRAMPOLINE else shape_b
            prop_shape = shape_b if tramp_shape is shape_a else shape_a

            trampoline: Optional[Trampoline] = getattr(tramp_shape, "trampoline_ref", None)
            if trampoline:
                trampoline.trigger_bounce(prop_shape.body)
                pts = int(100 * self.combo)
                self.coins += pts
                self.scoring.register_hit(pts, 1000.0, (prop_shape.body.position.x, prop_shape.body.position.y), COLOR_CYAN_GLOW)
                self._record_trick("MEGA TRAMPOLINE!", pts, COLOR_CYAN_GLOW)
                self.combo = min(10.0, self.combo + 0.3)
                self.combo_timer = 2.5

        self.physics_world.space.on_collision(
            COLLISION_TYPE_PROP,
            COLLISION_TYPE_TRAMPOLINE,
            post_solve=on_trampoline_hit
        )

        # 3. Wall / Hard Surface Impact on Ragdoll
        def on_wall_hit(arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> None:
            if self.state != GameModeState.PLAYING or not self.ragdoll:
                return
            impulse = arbiter.total_impulse.length
            if impulse > 120.0:
                coins = self.ragdoll.register_impact(impulse)
                if coins > 0:
                    self.coins += coins
                    contact = arbiter.contact_point_set.points[0].point_a if arbiter.contact_point_set.points else (self.ragdoll.torso.position.x, self.ragdoll.torso.position.y)
                    self.scoring.register_hit(coins, impulse, contact, COLOR_WHITE_BRIGHT)
                    if impulse > 450.0:
                        self._record_trick("WALL SLAM!", coins, COLOR_HAZARD_RED)

        self.physics_world.space.on_collision(
            COLLISION_TYPE_PROP,
            COLLISION_TYPE_WALL,
            post_solve=on_wall_hit
        )

    def _record_trick(self, name: str, points: int, color: Tuple[int, int, int]) -> None:
        self.recent_trick = TrickEvent(name=name, points=points, color=color, timestamp=time.time())

    def start(self) -> None:
        self.state = GameModeState.PLAYING
        self.coins = 0
        self.combo = 1.0
        self.combo_timer = 0.0
        self.recent_trick = None
        self._scream_cooldown = 0.0

        # Clean existing contraptions
        self._clean_contraptions()
        self.physics_world.clear_dynamic_bodies()

        w = float(self.physics_world.width)
        h = float(self.physics_world.height)
        space = self.physics_world.space

        # 1. Spawn Articulated Ragdoll "Buddy"
        self.ragdoll = Ragdoll(space, w * 0.5, h * 0.35, scale=1.1)

        # 2. Spawn 3 Neon Pinball Bumpers
        self.bumpers = [
            PinballBumper(space, w * 0.35, h * 0.40, radius=44.0),
            PinballBumper(space, w * 0.65, h * 0.40, radius=44.0),
            PinballBumper(space, w * 0.50, h * 0.62, radius=50.0),
        ]

        # 3. Spawn Wormhole Portals (Left & Right)
        self.portals = PortalPair(pos_a=(140.0, h * 0.45), pos_b=(w - 140.0, h * 0.45), radius=45.0)

        # 4. Spawn Floor Trampoline
        self.trampoline = Trampoline(space, w * 0.5, h - 25.0, width=220.0)

    def _clean_contraptions(self) -> None:
        if self.ragdoll:
            self.ragdoll.destroy()
            self.ragdoll = None
        for b in self.bumpers:
            b.destroy()
        self.bumpers.clear()
        if self.trampoline:
            self.trampoline.destroy()
            self.trampoline = None
        self.portals = None

    def update(self, dt: float) -> None:
        if self.state != GameModeState.PLAYING:
            return

        now = time.time()

        # Update contraptions
        for b in self.bumpers:
            b.update(dt)
        if self.trampoline:
            self.trampoline.update(dt)

        # Update wormhole portals
        if self.portals:
            jumps = self.portals.update_and_teleport(self.physics_world.get_dynamic_bodies(), dt, now)
            for src, dst in jumps:
                pts = int(250 * self.combo)
                self.coins += pts
                self.scoring.register_hit(pts, 1500.0, dst, COLOR_VIOLET_FLUX)
                self._record_trick("PORTAL WARP!", pts, COLOR_VIOLET_FLUX)
                self.combo = min(10.0, self.combo + 0.8)
                self.combo_timer = 2.5

        # Update ragdoll state
        if self.ragdoll:
            self.ragdoll.update(dt)

        # Combo decay
        if self.combo_timer > 0.0:
            self.combo_timer -= dt
            if self.combo_timer <= 0.0:
                self.combo = 1.0

        # Check trick expiration
        if self.recent_trick and now - self.recent_trick.timestamp > 1.8:
            self.recent_trick = None

    def reset(self) -> None:
        self.start()
