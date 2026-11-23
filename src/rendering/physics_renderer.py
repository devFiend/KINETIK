"""Renders Pymunk rigid bodies with neon cyberpunk aesthetics in Pygame."""
import math
from typing import List
import pygame
import pymunk

from src.config import COLOR_WHITE_BRIGHT
from src.physics.objects import PropType, PropVisualData


def render_physics_bodies(
    surface: pygame.Surface,
    bodies: List[pymunk.Body]
) -> None:
    """
    Renders all Pymunk dynamic rigid bodies onto a Pygame surface.
    - Shaded interior.
    - Outer luminous glow outline.
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

        if visual_data.prop_type == PropType.SPHERE:
            r = int(visual_data.radius)

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
            # Transform Pymunk Poly vertices to screen coordinates
            for shape in body.shapes:
                if isinstance(shape, pymunk.Poly):
                    points = [
                        (int(v.x), int(v.y))
                        for v in shape.get_vertices()
                    ]
                    # Fill box
                    pygame.draw.polygon(surface, primary, points)
                    # Glowing border
                    pygame.draw.polygon(surface, glow, points, 2)

                    # Center core dot
                    pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, (pos_x, pos_y), 3)
