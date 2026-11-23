"""Visual rendering of telekinetic targeting reticles and kinetic cursors."""
import math
from typing import List
import pygame
from src.config import (
    COLOR_CYAN_GLOW,
    COLOR_GOLD_AMBER,
    COLOR_HAZARD_RED,
    COLOR_VIOLET_FLUX,
    COLOR_WHITE_BRIGHT,
)
from src.gestures.detector import GestureType, HandGestureState


def render_gesture_cursor(
    surface: pygame.Surface,
    state: HandGestureState,
    font: pygame.font.Font
) -> None:
    """
    Renders an animated sci-fi telekinetic targeting cursor at the hand focal point.
    - Outer fixed targeting ring.
    - Contracting inner energy ring scaling with pinch factor.
    - Kinetic velocity trail projection.
    - Floating state tag.
    """
    cx, cy = int(state.screen_pos[0]), int(state.screen_pos[1])

    # Color selection based on gesture state
    if state.is_pinched:
        core_color = COLOR_GOLD_AMBER
        ring_color = COLOR_VIOLET_FLUX
        status_label = "GRAB / PINCH"
    elif state.gesture_type == GestureType.PUSH:
        core_color = COLOR_HAZARD_RED
        ring_color = COLOR_GOLD_AMBER
        status_label = "KINETIC PUSH"
    elif state.gesture_type == GestureType.RELEASE:
        core_color = COLOR_WHITE_BRIGHT
        ring_color = COLOR_CYAN_GLOW
        status_label = "RELEASE / FLING"
    else:
        core_color = COLOR_CYAN_GLOW
        ring_color = COLOR_CYAN_GLOW
        status_label = "HOVER"

    # Outer reticle brackets / ring (Radius = 26px)
    base_radius = 26
    pygame.draw.circle(surface, ring_color, (cx, cy), base_radius, 2)

    # Crosshair ticks
    tick_len = 6
    pygame.draw.line(surface, ring_color, (cx - base_radius - tick_len, cy), (cx - base_radius + 2, cy), 2)
    pygame.draw.line(surface, ring_color, (cx + base_radius - 2, cy), (cx + base_radius + tick_len, cy), 2)
    pygame.draw.line(surface, ring_color, (cx, cy - base_radius - tick_len), (cx, cy - base_radius + 2), 2)
    pygame.draw.line(surface, ring_color, (cx, cy + base_radius - 2), (cx, cy + base_radius + tick_len), 2)

    # Contracting inner pinch ring (Radius scales from base_radius down to 6px)
    pinch_progress = state.pinch_factor
    inner_radius = int(base_radius - pinch_progress * (base_radius - 6))
    inner_radius = max(5, inner_radius)
    pygame.draw.circle(surface, core_color, (cx, cy), inner_radius, 2)

    # Central focal dot
    dot_radius = 4 if state.is_pinched else 3
    pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, (cx, cy), dot_radius)

    # Velocity trajectory vector projection (if speed > 100 px/s)
    if state.speed > 100.0:
        trail_length = min(80.0, state.speed * 0.04)
        angle = math.atan2(state.velocity[1], state.velocity[0])
        tx = int(cx + math.cos(angle) * trail_length)
        ty = int(cy + math.sin(angle) * trail_length)
        pygame.draw.line(surface, core_color, (cx, cy), (tx, ty), 2)
        pygame.draw.circle(surface, core_color, (tx, ty), 3)

    # Floating state tag badge
    badge_surf = font.render(f"{state.handedness}: {status_label}", True, core_color)
    surface.blit(badge_surf, (cx + base_radius + 10, cy - 10))


def render_all_cursors(
    surface: pygame.Surface,
    gesture_states: List[HandGestureState],
    font: pygame.font.Font
) -> None:
    """Render cursors for all active gesture hands."""
    for state in gesture_states:
        render_gesture_cursor(surface, state, font)
