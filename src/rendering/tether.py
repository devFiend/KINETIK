"""Visual rendering of telekinetic energy tethers, lightning arcs, and force auras."""
import math
import random
import time
from typing import List, Tuple
import pygame
import pymunk

from src.config import COLOR_CYAN_GLOW, COLOR_GOLD_AMBER, COLOR_VIOLET_FLUX, COLOR_WHITE_BRIGHT


def render_energy_tether(
    surface: pygame.Surface,
    hand_pos: Tuple[float, float],
    body_pos: Tuple[float, float],
    color: Tuple[int, int, int] = COLOR_CYAN_GLOW,
    segments: int = 12,
    amplitude: float = 8.0
) -> None:
    """
    Renders an electric lightning telekinetic tether connecting the hand cursor
    to the held object's center of mass with animated sine-wave lightning vibrations.
    """
    hx, hy = hand_pos
    bx, by = body_pos

    dx = bx - hx
    dy = by - hy
    total_dist = math.hypot(dx, dy)
    if total_dist < 2.0:
        return

    # Normal perpendicular vector for displacement
    nx = -dy / total_dist
    ny = dx / total_dist

    t = time.time() * 18.0  # High-frequency vibration

    points: List[Tuple[int, int]] = [(int(hx), int(hy))]

    for i in range(1, segments):
        frac = i / segments
        base_x = hx + dx * frac
        base_y = hy + dy * frac

        # Sine wave displacement combined with micro jitter
        sine_disp = math.sin(t + frac * 12.0) * amplitude * math.sin(frac * math.pi)
        jitter = random.uniform(-2.0, 2.0)
        disp = sine_disp + jitter

        px = int(base_x + nx * disp)
        py = int(base_y + ny * disp)
        points.append((px, py))

    points.append((int(bx), int(by)))

    # Draw outer electric glow
    pygame.draw.lines(surface, color, False, points, 3)
    # Draw hot white inner core
    pygame.draw.lines(surface, COLOR_WHITE_BRIGHT, False, points, 1)

    # Luminous halo around held body
    pygame.draw.circle(surface, COLOR_GOLD_AMBER, (int(bx), int(by)), 32, 2)
