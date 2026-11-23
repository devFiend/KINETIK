"""Object-pooled 2D particle simulation engine for trails, sparks, and impact bursts."""
import math
import random
from typing import List, Tuple
import pygame

from src.config import COLOR_CYAN_GLOW, COLOR_GOLD_AMBER, COLOR_VIOLET_FLUX, COLOR_WHITE_BRIGHT


class Particle:
    """Individual particle state."""

    def __init__(self):
        self.active: bool = False
        self.x: float = 0.0
        self.y: float = 0.0
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.radius: float = 2.0
        self.color: Tuple[int, int, int] = COLOR_CYAN_GLOW
        self.life: float = 0.0
        self.max_life: float = 1.0

    def spawn(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: Tuple[int, int, int],
        radius: float = 3.0,
        lifetime: float = 0.4
    ) -> None:
        self.active = True
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius
        self.life = lifetime
        self.max_life = max(1e-3, lifetime)

    def update(self, dt: float) -> bool:
        """Advance particle physics. Returns True if particle remains alive."""
        if not self.active:
            return False

        self.life -= dt
        if self.life <= 0.0:
            self.active = False
            return False

        self.x += self.vx * dt
        self.y += self.vy * dt
        # Drag damping
        self.vx *= (1.0 - 1.5 * dt)
        self.vy *= (1.0 - 1.5 * dt)
        return True


class ParticlePool:
    """
    Fixed-size object pool for particles.
    Zero garbage collection overhead during high-frequency gameplay.
    """

    def __init__(self, pool_size: int = 500):
        self.pool_size = pool_size
        self.particles: List[Particle] = [Particle() for _ in range(pool_size)]
        self._next_idx: int = 0

    def _get_particle(self) -> Particle:
        """Get the next slot in the ring pool."""
        p = self.particles[self._next_idx]
        self._next_idx = (self._next_idx + 1) % self.pool_size
        return p

    def emit_burst(
        self,
        x: float,
        y: float,
        count: int = 16,
        color: Tuple[int, int, int] = COLOR_CYAN_GLOW,
        speed_min: float = 60.0,
        speed_max: float = 280.0
    ) -> None:
        """Emit radial burst of sparks (e.g. on collision impact)."""
        for _ in range(count):
            p = self._get_particle()
            angle = random.uniform(0.0, 2.0 * math.pi)
            speed = random.uniform(speed_min, speed_max)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            radius = random.uniform(2.0, 4.0)
            lifetime = random.uniform(0.2, 0.5)
            p.spawn(x, y, vx, vy, color, radius=radius, lifetime=lifetime)

    def emit_trail(
        self,
        x: float,
        y: float,
        color: Tuple[int, int, int] = COLOR_VIOLET_FLUX,
        radius: float = 3.0
    ) -> None:
        """Emit soft fading trail mote behind high-speed objects."""
        p = self._get_particle()
        vx = random.uniform(-15.0, 15.0)
        vy = random.uniform(-15.0, 15.0)
        p.spawn(x, y, vx, vy, color, radius=radius, lifetime=0.25)

    def emit_clash_nova(self, x: float, y: float) -> None:
        """Emit high-energy multi-colored particle nova on dual-hand prop clash."""
        colors = [COLOR_GOLD_AMBER, COLOR_VIOLET_FLUX, COLOR_WHITE_BRIGHT, COLOR_CYAN_GLOW]
        for _ in range(48):
            p = self._get_particle()
            angle = random.uniform(0.0, 2.0 * math.pi)
            speed = random.uniform(150.0, 650.0)
            p.spawn(
                x, y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                color=random.choice(colors),
                radius=random.uniform(3.0, 6.0),
                lifetime=random.uniform(0.4, 0.8)
            )

    def emit_singularity_motes(self, cx: float, cy: float) -> None:
        """Emit inward-spiral suction motes for the black hole vortex."""
        for _ in range(6):
            p = self._get_particle()
            angle = random.uniform(0.0, 2.0 * math.pi)
            dist = random.uniform(120.0, 320.0)
            sx = cx + math.cos(angle) * dist
            sy = cy + math.sin(angle) * dist
            # Aim inward towards center with tangential spin
            vx = -math.cos(angle) * 350.0 - math.sin(angle) * 120.0
            vy = -math.sin(angle) * 350.0 + math.cos(angle) * 120.0
            p.spawn(sx, sy, vx, vy, COLOR_VIOLET_FLUX, radius=random.uniform(2.0, 4.0), lifetime=0.45)

    def update(self, dt: float) -> int:
        """Update all active particles. Returns count of active particles."""
        active_count = 0
        for p in self.particles:
            if p.active:
                if p.update(dt):
                    active_count += 1
        return active_count

    def draw(self, surface: pygame.Surface) -> None:
        """Render all active particles onto display surface with fadeout."""
        for p in self.particles:
            if not p.active:
                continue

            # Scale radius down with remaining life
            fraction = p.life / p.max_life
            r = max(1, int(p.radius * fraction))
            pygame.draw.circle(surface, p.color, (int(p.x), int(p.y)), r)
