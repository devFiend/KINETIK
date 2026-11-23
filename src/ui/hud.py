"""Presentation HUD and telemetry renderer for Target Rush, Free Play, and Progression."""
import math
from typing import List, Optional
import pygame
import pymunk

from src.config import (
    COLOR_CYAN_GLOW,
    COLOR_GOLD_AMBER,
    COLOR_HAZARD_RED,
    COLOR_HUD_TEXT,
    COLOR_VIOLET_FLUX,
    COLOR_WHITE_BRIGHT,
)
from src.game.modes import BaseGameMode, GameModeState, ModeType, TargetRushMode
from src.game.progression import ProgressionManager
from src.game.scoring import ScoringEngine
from src.gestures.detector import HandGestureState
from src.physics.targets import TargetDrone


def render_game_hud(
    surface: pygame.Surface,
    mode: BaseGameMode,
    scoring: ScoringEngine,
    progression: ProgressionManager,
    primary_hand: Optional[HandGestureState],
    targeted_body: Optional[pymunk.Body],
    is_holding: bool,
    fonts: dict,
    screen_width: int,
    screen_height: int
) -> None:
    """Renders real-time game mode HUD, telekinesis cues, timer, and score."""
    title_font = fonts["title"]
    font = fonts["font"]
    big_font = fonts["big"]
    small_font = fonts["small"]

    # Top mode header
    mode_text = f"MODE: {mode.mode_type.value}"
    surface.blit(title_font.render(mode_text, True, COLOR_CYAN_GLOW), (30, 22))

    # Player Rank & Progression Header
    rank = progression.current_rank
    rank_badge = f"RANK: {rank.name.upper()} ({progression.profile.total_xp:,} XP)"
    surface.blit(small_font.render(rank_badge, True, COLOR_GOLD_AMBER), (30, 48))

    # Rank Progress Mini-Bar (Width = 120px)
    px, py = 30, 64
    pygame.draw.rect(surface, (30, 40, 55), (px, py, 120, 4))
    fill_px = int(120 * progression.rank_progress_fraction)
    if fill_px > 0:
        pygame.draw.rect(surface, COLOR_GOLD_AMBER, (px, py, fill_px, 4))

    # Real-Time Telekinesis Guidance Status
    if is_holding:
        guide_status = "⚡ HOLDING OBJECT! Move hand to steer, flick wrist & open pinch to THROW!"
        guide_color = COLOR_GOLD_AMBER
    elif targeted_body is not None:
        if primary_hand and primary_hand.is_pinched:
            guide_status = "🎯 OBJECT LOCKED & PINCHED — Grabbing!"
            guide_color = COLOR_WHITE_BRIGHT
        else:
            guide_status = "🎯 OBJECT IN REACH! Pinch thumb & index together to GRAB!"
            guide_color = COLOR_CYAN_GLOW
    elif primary_hand is not None:
        pinch_str = "PINCH: CLOSED" if primary_hand.is_pinched else f"PINCH: OPEN (Dist: {primary_hand.pinch_distance:.2f})"
        guide_status = f"🖐️ Hand Active | {pinch_str} | Move near any ball to target!"
        guide_color = COLOR_HUD_TEXT
    else:
        guide_status = "⚠️ No Hand Detected — Raise your hand in front of the camera!"
        guide_color = COLOR_HAZARD_RED

    surface.blit(font.render(guide_status, True, guide_color), (30, 76))

    # Display recent unlocks / achievement banners
    if progression.recent_unlocks:
        latest = progression.recent_unlocks[-1]
        surface.blit(small_font.render(latest, True, COLOR_VIOLET_FLUX), (30, 102))

    if isinstance(mode, TargetRushMode):
        # 1. Round Timer Countdown
        time_color = COLOR_HAZARD_RED if mode.time_remaining <= 10.0 else COLOR_WHITE_BRIGHT
        timer_text = f"TIME: {mode.time_remaining:04.1f}s"
        surface.blit(big_font.render(timer_text, True, time_color), (screen_width - 260, 22))

        # 2. Score & Multiplier
        score_text = f"SCORE: {scoring.score:,}"
        surface.blit(big_font.render(score_text, True, COLOR_GOLD_AMBER), (screen_width - 260, 62))

        # 3. Combo Multiplier Badge & Decay Gauge
        mult = scoring.combo_multiplier
        mult_text = f"{mult:.1f}x COMBO"
        mult_color = COLOR_VIOLET_FLUX if mult >= 3.0 else COLOR_CYAN_GLOW
        surface.blit(font.render(mult_text, True, mult_color), (screen_width - 260, 100))

        # Combo Decay Bar (Width = 140px)
        gauge_width = 140
        gauge_height = 6
        gx, gy = screen_width - 260, 125
        pygame.draw.rect(surface, (40, 50, 70), (gx, gy, gauge_width, gauge_height))
        fill_w = int(gauge_width * scoring.combo_decay_fraction)
        if fill_w > 0:
            pygame.draw.rect(surface, mult_color, (gx, gy, fill_w, gauge_height))

        # Draw floating target hit scores
        for fs in scoring.floating_scores:
            pop_surf = font.render(f"+{fs.points}", True, fs.color)
            surface.blit(pop_surf, (int(fs.x), int(fs.y)))

        # 4. Round Over Victory / Summary Overlay
        if mode.state == GameModeState.ROUND_OVER:
            panel_w, panel_h = 560, 340
            px = (screen_width - panel_w) // 2
            py = (screen_height - panel_h) // 2

            panel_surf = pygame.Surface((panel_w, panel_h))
            panel_surf.fill((11, 14, 24))
            panel_surf.set_alpha(240)
            surface.blit(panel_surf, (px, py))
            pygame.draw.rect(surface, COLOR_CYAN_GLOW, (px, py, panel_w, panel_h), 2)

            surface.blit(big_font.render("ROUND COMPLETE", True, COLOR_GOLD_AMBER), (px + 160, py + 30))
            surface.blit(font.render(f"FINAL SCORE: {scoring.score:,}", True, COLOR_WHITE_BRIGHT), (px + 60, py + 95))
            surface.blit(font.render(f"BEST RECORD: {progression.profile.best_target_rush_score:,}", True, COLOR_GOLD_AMBER), (px + 60, py + 125))
            surface.blit(font.render(f"TARGETS HIT: {scoring.total_hits}", True, COLOR_HUD_TEXT), (px + 60, py + 155))
            surface.blit(font.render(f"MAX COMBO: {scoring.max_combo:.1f}x", True, COLOR_VIOLET_FLUX), (px + 60, py + 185))
            surface.blit(font.render(f"RANK: {progression.current_rank.name} ({progression.profile.total_xp:,} XP)", True, COLOR_CYAN_GLOW), (px + 60, py + 215))

            surface.blit(font.render("Press [R] or [SPACE] to Restart Round", True, COLOR_CYAN_GLOW), (px + 95, py + 280))


def render_target_drones(surface: pygame.Surface, targets: List[TargetDrone]) -> None:
    """Render floating animated target drones with rotating crosshairs and pulsing cores."""
    for drone in targets:
        if not drone.alive:
            continue

        tx = int(drone.body.position.x)
        ty = int(drone.body.position.y)
        r = int(drone.radius)

        pygame.draw.circle(surface, drone.color, (tx, ty), r + 4, 2)
        pygame.draw.circle(surface, drone.color, (tx, ty), r)
        pygame.draw.circle(surface, COLOR_WHITE_BRIGHT, (tx, ty), max(2, int(r * 0.35)))

        angle = drone.time_alive * 2.0
        for i in range(4):
            a = angle + (i * math.pi / 2.0)
            x1 = int(tx + math.cos(a) * (r + 2))
            y1 = int(ty + math.sin(a) * (r + 2))
            x2 = int(tx + math.cos(a) * (r + 8))
            y2 = int(ty + math.sin(a) * (r + 8))
            pygame.draw.line(surface, drone.color, (x1, y1), (x2, y2), 2)
