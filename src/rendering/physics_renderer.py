"""Renders Pymunk rigid bodies with neon cyberpunk aesthetics in Pygame."""
import math
from typing import List, Optional
import pygame
import pymunk

from src.config import COLOR_CYAN_GLOW, COLOR_GOLD_AMBER, COLOR_WHITE_BRIGHT
from src.physics.objects import PropType, PropVisualData


def render_physics_bodies(
    surface: pygame.Surface,
    bodies: List[pymunk.Body],
    targeted_body: Optional[pymunk.Body] = None
) -> None:
    """
    Renders all Pymunk dynamic rigid bodies onto a Pygame surface.
    - Shaded interior.
    - Outer luminous glow outline.
    - Targeting reticle brackets if body is in reach of hand.
    - Golden aura if body is actively held.
    - Orientation tick/radial line showing physical spin/rotation.
    """
    for body in bodies:
        visual_data: PropVisualData = getattr(body, "custom_data", None)
        if visual_data is None:
            continue

        pos_x = int(body.position.x)
        pos_y = int(body.position.y)
        angle = body.angle

        primary = visual_data.primary_color
        glow = visual_data.glow_color
        is_held = getattr(visual_data, "is_held", False)
        is_targeted = (body is targeted_body) and not is_held

        if visual_data.prop_type == PropType.SPHERE:
            r = int(visual_data.radius)

            # Held golden aura
            if is_held:
                pygame.draw.circle(surface, COLOR_GOLD_AMBER, (pos_x, pos_y), r + 8, 2)
            # In-reach targeting lock ring
            elif is_targeted:
                pygame.draw.circle(surface, COLOR_CYAN_GLOW, (pos_x, pos_y), r + 6, 2)
                # Targeting tick brackets
                pygame.draw.line(surface, COLOR_CYAN_GLOW, (pos_x - r - 10, pos_y), (pos_x - r - 4, pos_y), 2)
                pygame.draw.line(surface, COLOR_CYAN_GLOW, (pos_x + r + 4, pos_y), (pos_x + r + 10, pos_y), 2)
                pygame.draw.line(surface, COLOR_CYAN_GLOW, (pos_x, pos_y - r - 10), (pos_x, pos_y - r - 4), 2)
                pygame.draw.line(surface, COLOR_CYAN_GLOW, (pos_x, pos_y + r + 4), (pos_x, pos_y + r + 10), 2)

            # Outer glow halo
            pygame.draw.circle(surface, primary, (pos_x, pos_y), r + 2, 2)
            # Body fill
            pygame.draw.circle(surface, primary, (pos_x, pos_y), r)
            # Highlight glint
            glint_x = int(pos_x - r * 0.3)
            glint_y = int(pos_y - r * 0.3)
            pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, (glint_x, glint_y), max(2, int(r * 0.25)))

            # Rotation spoke
            spoke_x = int(pos_x + math.cos(angle) * (r - 4))
            spoke_y = int(pos_y + math.sin(angle) * (r - 4))
            pygame.draw.line(surface, (20, 25, 35), (pos_x, pos_y), (spoke_x, spoke_y), 2)

        elif visual_data.prop_type == PropType.BOX:
            for shape in body.shapes:
                if isinstance(shape, pymunk.Poly):
                    points = [
                        (int(v.x), int(v.y))
                        for v in shape.get_vertices()
                    ]
                    pygame.draw.polygon(surface, primary, points)
                    border_color = COLOR_GOLD_AMBER if is_held else (COLOR_CYAN_GLOW if is_targeted else glow)
                    pygame.draw.polygon(surface, border_color, points, 3 if (is_held or is_targeted) else 2)
                    pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, (pos_x, pos_y), 3)
