"""Pygame rendering routines for MediaPipe hand skeletons and glowing landmark nodes."""
from typing import List, Tuple
import pygame
from src.camera.hand_tracker import HAND_CONNECTIONS, HandData
from src.config import COLOR_CYAN_GLOW, COLOR_VIOLET_FLUX, COLOR_WHITE_BRIGHT


def render_hand_skeleton(
    surface: pygame.Surface,
    hands: List[HandData],
    screen_width: int,
    screen_height: int,
    primary_color: Tuple[int, int, int] = COLOR_CYAN_GLOW,
    joint_radius: int = 5,
    bone_width: int = 2
) -> None:
    """
    Render glowing hand bones and joints onto a Pygame display surface.
    Coordinates are transformed from normalized [0..1] space into screen pixel space.
    """
    for hand in hands:
        # Precompute screen coordinate mapping
        screen_points = [
            (int(lm.x * screen_width), int(lm.y * screen_height))
            for lm in hand.landmarks
        ]

        # Draw bones / connections
        for start_idx, end_idx in HAND_CONNECTIONS:
            start_pos = screen_points[start_idx]
            end_pos = screen_points[end_idx]

            # Subtle outer glow for bones
            pygame.draw.line(surface, primary_color, start_pos, end_pos, bone_width)

        # Draw joint nodes
        for idx, (px, py) in enumerate(screen_points):
            # Thumb tip (4) and Index tip (8) get larger highlighted nodes
            if idx in (4, 8):
                pygame.draw.circle(surface, COLOR_VIOLET_FLUX, (px, py), joint_radius + 3)
                pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, (px, py), joint_radius)
            else:
                pygame.draw.circle(surface, primary_color, (px, py), joint_radius)
                pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, (px, py), max(1, joint_radius - 2))
