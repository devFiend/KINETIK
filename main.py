#!/usr/bin/env python3
"""
KINETIK — Webcam-Powered Telekinesis Playground
Application Entry Point (P0 Foundation)
"""
import argparse
import os
import sys
import pygame

from src.config import (
    WINDOW_TITLE,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    TARGET_FPS,
    COLOR_BACKGROUND,
    COLOR_CYAN_GLOW,
    COLOR_HUD_TEXT
)


def run(headless: bool = False, max_frames: int = 0) -> int:
    """Initialize Pygame and run application lifecycle."""
    if headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Consolas", 20)
    title_font = pygame.font.SysFont("Consolas", 36, bold=True)

    running = True
    frame_count = 0

    print(f"[KINETIK] Initialized successfully. Target FPS: {TARGET_FPS}, Headless: {headless}")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

        # Clear screen with obsidian theme
        screen.fill(COLOR_BACKGROUND)

        # Render placeholder P0 HUD
        title_surf = title_font.render("KINETIK // PHASE P0 FOUNDATION", True, COLOR_CYAN_GLOW)
        screen.blit(title_surf, (40, 40))

        status_text = (
            f"FPS: {clock.get_fps():.1f} | Frame: {frame_count} | Press ESC or Q to quit"
        )
        status_surf = font.render(status_text, True, COLOR_HUD_TEXT)
        screen.blit(status_surf, (40, 90))

        hint_surf = font.render("Ready for Phase P1 Vision Pipeline Ingestion", True, (120, 150, 170))
        screen.blit(hint_surf, (40, 130))

        pygame.display.flip()
        clock.tick(TARGET_FPS)
        frame_count += 1

        if max_frames > 0 and frame_count >= max_frames:
            print(f"[KINETIK] Reached requested max_frames={max_frames}, exiting cleanly.")
            running = False

    pygame.quit()
    return 0


def main():
    parser = argparse.ArgumentParser(description="KINETIK Telekinesis Playground")
    parser.add_argument("--headless", action="store_true", help="Run in headless SDL mode (for CI/automated test)")
    parser.add_argument("--test-frames", type=int, default=0, help="Run for N frames and exit (for verification)")
    args = parser.parse_args()

    return run(headless=args.headless, max_frames=args.test_frames)


if __name__ == "__main__":
    sys.exit(main())
