"""Presentation renderer for articulated Ragdoll characters, facial expressions, and playground contraptions."""
import math
import time
from typing import List, Tuple
import pygame
import pymunk

from src.config import (
    COLOR_CYAN_GLOW,
    COLOR_GOLD_AMBER,
    COLOR_HAZARD_RED,
    COLOR_VIOLET_FLUX,
    COLOR_WHITE_BRIGHT,
)
from src.physics.contraptions import PinballBumper, PortalPair, Trampoline
from src.physics.ragdoll import Ragdoll, RagdollExpression


def draw_capsule(
    surface: pygame.Surface,
    body: pymunk.Body,
    width: float,
    height: float,
    color: Tuple[int, int, int],
    border_color: Tuple[int, int, int] = (20, 30, 45)
) -> None:
    """Draw rotated rounded rectangular limb segment."""
    angle = body.angle
    cx, cy = body.position.x, body.position.y

    # Create local surface for limb
    surf_w = int(max(width, height) * 2.0)
    surf_h = surf_w
    limb_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)

    # Draw rounded rectangle in center
    rect_x = (surf_w - width) * 0.5
    rect_y = (surf_h - height) * 0.5
    r = int(min(width, height) * 0.45)
    pygame.draw.rect(limb_surf, color, (rect_x, rect_y, width, height), border_radius=r)
    pygame.draw.rect(limb_surf, border_color, (rect_x, rect_y, width, height), width=2, border_radius=r)

    # Rotate and blit
    rot_surf = pygame.transform.rotate(limb_surf, -math.degrees(angle))
    rot_rect = rot_surf.get_rect(center=(int(cx), int(cy)))
    surface.blit(rot_surf, rot_rect)


def render_ragdoll(surface: pygame.Surface, ragdoll: Ragdoll) -> None:
    """Render full articulated ragdoll with limbs, joints, and expressive face."""
    s = ragdoll.scale

    # 1. Draw Legs
    draw_capsule(surface, ragdoll.left_thigh, 12.0 * s, 28.0 * s, (40, 80, 180))
    draw_capsule(surface, ragdoll.left_shin, 10.0 * s, 26.0 * s, (30, 40, 60))
    draw_capsule(surface, ragdoll.right_thigh, 12.0 * s, 28.0 * s, (40, 80, 180))
    draw_capsule(surface, ragdoll.right_shin, 10.0 * s, 26.0 * s, (30, 40, 60))

    # 2. Draw Torso
    draw_capsule(surface, ragdoll.torso, 26.0 * s, 54.0 * s, (60, 140, 240))

    # 3. Draw Arms
    draw_capsule(surface, ragdoll.left_arm, 10.0 * s, 24.0 * s, (80, 160, 255))
    draw_capsule(surface, ragdoll.left_forearm, 9.0 * s, 22.0 * s, (255, 210, 160))
    draw_capsule(surface, ragdoll.right_arm, 10.0 * s, 24.0 * s, (80, 160, 255))
    draw_capsule(surface, ragdoll.right_forearm, 9.0 * s, 22.0 * s, (255, 210, 160))

    # 4. Draw Head
    hx, hy = int(ragdoll.head.position.x), int(ragdoll.head.position.y)
    hr = int(18.0 * s)
    h_angle = ragdoll.head.angle

    # Head shadow / outline
    pygame.draw.circle(surface, (20, 30, 45), (hx, hy), hr + 2)
    # Head skin
    pygame.draw.circle(surface, (255, 210, 160), (hx, hy), hr)

    # 5. Draw Facial Expressions (oriented with head angle)
    cos_a = math.cos(h_angle)
    sin_a = math.sin(h_angle)

    def rot_pt(lx: float, ly: float) -> Tuple[int, int]:
        rx = lx * cos_a - ly * sin_a
        ry = lx * sin_a + ly * cos_a
        return (int(hx + rx), int(hy + ry))

    expr = ragdoll.expression

    if expr == RagdollExpression.HAPPY:
        # Happy arched eyes
        e1 = rot_pt(-6.0 * s, -4.0 * s)
        e2 = rot_pt(6.0 * s, -4.0 * s)
        pygame.draw.circle(surface, (30, 30, 40), e1, max(2, int(3.0 * s)))
        pygame.draw.circle(surface, (30, 30, 40), e2, max(2, int(3.0 * s)))
        # Smile
        m1 = rot_pt(-5.0 * s, 4.0 * s)
        m2 = rot_pt(0.0 * s, 7.0 * s)
        m3 = rot_pt(5.0 * s, 4.0 * s)
        pygame.draw.lines(surface, (30, 30, 40), False, [m1, m2, m3], max(2, int(2.0 * s)))

    elif expr == RagdollExpression.PANIC_SCREAM:
        # Huge dilated panic eyes
        e1 = rot_pt(-7.0 * s, -4.0 * s)
        e2 = rot_pt(7.0 * s, -4.0 * s)
        pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, e1, max(3, int(5.0 * s)))
        pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, e2, max(3, int(5.0 * s)))
        pygame.draw.circle(surface, (20, 20, 30), e1, max(1, int(2.0 * s)))
        pygame.draw.circle(surface, (20, 20, 30), e2, max(1, int(2.0 * s)))
        # Wide open screaming mouth
        mc = rot_pt(0.0, 5.0 * s)
        pygame.draw.circle(surface, (180, 30, 40), mc, max(3, int(6.0 * s)))
        pygame.draw.circle(surface, (30, 10, 20), mc, max(2, int(4.0 * s)))

    elif expr == RagdollExpression.DIZZY:
        # Spiral / Swirl dizzy eyes @_@
        for sign in (-1, 1):
            ec = rot_pt(sign * 6.5 * s, -4.0 * s)
            pygame.draw.circle(surface, (80, 50, 120), ec, max(3, int(4.5 * s)), width=1)
            pygame.draw.circle(surface, COLOR_VIOLET_FLUX, ec, max(1, int(2.0 * s)))
        # Wavy dizzy mouth
        m1 = rot_pt(-6.0 * s, 4.0 * s)
        m2 = rot_pt(-2.0 * s, 6.0 * s)
        m3 = rot_pt(2.0 * s, 3.0 * s)
        m4 = rot_pt(6.0 * s, 5.0 * s)
        pygame.draw.lines(surface, (60, 40, 80), False, [m1, m2, m3, m4], 2)

    elif expr == RagdollExpression.GRABBED:
        # Surprised wide eyes
        e1 = rot_pt(-6.0 * s, -5.0 * s)
        e2 = rot_pt(6.0 * s, -5.0 * s)
        pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, e1, max(2, int(4.0 * s)))
        pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, e2, max(2, int(4.0 * s)))
        pygame.draw.circle(surface, (30, 30, 40), e1, max(1, int(2.0 * s)))
        pygame.draw.circle(surface, (30, 30, 40), e2, max(1, int(2.0 * s)))
        # Surprised "O" mouth
        mc = rot_pt(0.0, 4.0 * s)
        pygame.draw.circle(surface, (40, 40, 50), mc, max(2, int(3.5 * s)), width=2)


def render_contraptions(
    surface: pygame.Surface,
    bumpers: List[PinballBumper],
    portals: Optional[PortalPair],
    trampoline: Optional[Trampoline],
    now: float
) -> None:
    """Render animated neon pinball bumpers, spinning portal rifts, and trampoline."""
    # 1. Pinball Bumpers
    for b in bumpers:
        bx, by = int(b.x), int(b.y)
        r = int(b.radius)

        # Flashing explosion ring when struck
        if b.flash_timer > 0.0:
            flash_r = r + int((0.25 - b.flash_timer) * 120.0)
            pygame.draw.circle(surface, COLOR_GOLD_AMBER, (bx, by), flash_r, 3)

        # Base bumper disc
        pygame.draw.circle(surface, (25, 30, 48), (bx, by), r)
        pygame.draw.circle(surface, COLOR_CYAN_GLOW, (bx, by), r, 3)
        pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, (bx, by), max(3, int(r * 0.4)))
        pygame.draw.circle(surface, COLOR_GOLD_AMBER, (bx, by), max(2, int(r * 0.2)))

    # 2. Wormhole Portals
    if portals:
        # Portal A (Cyan/Blue)
        pa_x, pa_y = int(portals.pos_a[0]), int(portals.pos_a[1])
        pr = int(portals.radius)
        spin_a = now * 4.0

        for i in range(3):
            sub_r = pr - i * 8
            if sub_r > 4:
                pygame.draw.circle(surface, COLOR_CYAN_GLOW, (pa_x, pa_y), sub_r, 2)
        # Swirl particle spoke
        for k in range(4):
            ang = spin_a + k * (math.pi * 0.5)
            x2 = int(pa_x + math.cos(ang) * (pr - 4))
            y2 = int(pa_y + math.sin(ang) * (pr - 4))
            pygame.draw.line(surface, COLOR_WHITE_BRIGHT, (pa_x, pa_y), (x2, y2), 2)

        # Portal B (Orange/Amber)
        pb_x, pb_y = int(portals.pos_b[0]), int(portals.pos_b[1])
        spin_b = -now * 4.0
        for i in range(3):
            sub_r = pr - i * 8
            if sub_r > 4:
                pygame.draw.circle(surface, COLOR_GOLD_AMBER, (pb_x, pb_y), sub_r, 2)
        for k in range(4):
            ang = spin_b + k * (math.pi * 0.5)
            x2 = int(pb_x + math.cos(ang) * (pr - 4))
            y2 = int(pb_y + math.sin(ang) * (pr - 4))
            pygame.draw.line(surface, COLOR_WHITE_BRIGHT, (pb_x, pb_y), (x2, y2), 2)

    # 3. Trampoline
    if trampoline:
        tx, ty = int(trampoline.x), int(trampoline.y)
        hw = int(trampoline.width * 0.5)
        bounce_dip = int(math.sin(trampoline.bounce_timer * 15.0) * 8.0) if trampoline.bounce_timer > 0.0 else 0

        # Draw spring zig-zag under pad
        pygame.draw.line(surface, (80, 90, 110), (tx - hw + 20, ty + 18), (tx - hw + 20, ty + bounce_dip), 3)
        pygame.draw.line(surface, (80, 90, 110), (tx + hw - 20, ty + 18), (tx + hw - 20, ty + bounce_dip), 3)

        # Draw glowing bouncy top bar
        pad_color = COLOR_GOLD_AMBER if trampoline.bounce_timer > 0.0 else COLOR_CYAN_GLOW
        pygame.draw.line(surface, pad_color, (tx - hw, ty + bounce_dip), (tx + hw, ty + bounce_dip), 6)
        pygame.draw.line(surface, COLOR_WHITE_BRIGHT, (tx - hw + 10, ty + bounce_dip), (tx + hw - 10, ty + bounce_dip), 2)
