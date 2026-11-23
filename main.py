#!/usr/bin/env python3
"""
KINETIK — Webcam-Powered Telekinesis Playground
Application Entry Point with Phase P1 Vision Pipeline
"""
import argparse
import os
import sys
import cv2
import pygame

from src.camera.hand_tracker import HandTracker
from src.camera.webcam import WebcamCapture
from src.config import (
    COLOR_BACKGROUND,
    COLOR_CYAN_GLOW,
    COLOR_HAZARD_RED,
    COLOR_HUD_TEXT,
    COLOR_VIOLET_FLUX,
    COLOR_WHITE_BRIGHT,
    DEFAULT_CAM_HEIGHT,
    DEFAULT_CAM_WIDTH,
    DEFAULT_CAMERA_INDEX,
    DEFAULT_MIRROR_MODE,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    TARGET_FPS,
    WINDOW_TITLE,
)
from src.rendering.landmarks import render_hand_skeleton


def run(
    headless: bool = False,
    max_frames: int = 0,
    mock_camera: bool = False,
    camera_index: int = DEFAULT_CAMERA_INDEX
) -> int:
    """Initialize camera, vision engine, and Pygame lifecycle."""
    if headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Consolas", 18)
    title_font = pygame.font.SysFont("Consolas", 24, bold=True)
    status_font = pygame.font.SysFont("Consolas", 14)

    # Initialize Phase P1 Vision Pipeline
    print(f"[KINETIK] Initializing webcam capture on index={camera_index}...")
    webcam = WebcamCapture(
        camera_index=camera_index,
        width=DEFAULT_CAM_WIDTH,
        height=DEFAULT_CAM_HEIGHT,
        mirror=DEFAULT_MIRROR_MODE,
        mock_mode=mock_camera
    )
    cam_started = webcam.start()
    if not cam_started:
        print(f"[KINETIK WARNING] Webcam failed to start: {webcam.error_message}")

    print("[KINETIK] Initializing MediaPipe HandTracker...")
    tracker = HandTracker()

    running = True
    frame_count = 0
    show_camera_feed = True
    show_skeleton = True

    print("[KINETIK] Vision loop initialized. Controls: [M]irror, [C]amera toggle, [S]keleton, [ESC/Q]uit")

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_m:
                        webcam.toggle_mirror()
                        print(f"[KINETIK] Mirror mode: {webcam.mirror}")
                    elif event.key == pygame.K_c:
                        show_camera_feed = not show_camera_feed
                    elif event.key == pygame.K_s:
                        show_skeleton = not show_skeleton

            # Ingest freshest frame from threaded capture
            frame_bgr, _ = webcam.get_latest_frame()
            hands = []

            if frame_bgr is not None:
                # Run MediaPipe hand landmark inference
                hands = tracker.process_frame(frame_bgr)

            # --- Presentation Rendering ---
            # Fill background
            screen.fill(COLOR_BACKGROUND)

            # Draw camera feed if available and enabled
            if show_camera_feed and frame_bgr is not None:
                # Convert OpenCV BGR to RGB and scale to window surface
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                # Transpose and convert to Pygame Surface
                frame_surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                frame_surf = pygame.transform.scale(frame_surf, (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
                # Apply slight dimming so futuristic HUD and effects pop
                frame_surf.set_alpha(190)
                screen.blit(frame_surf, (0, 0))

            # Draw glowing hand skeleton overlays
            if show_skeleton and hands:
                render_hand_skeleton(
                    screen,
                    hands,
                    DEFAULT_WINDOW_WIDTH,
                    DEFAULT_WINDOW_HEIGHT,
                    primary_color=COLOR_CYAN_GLOW
                )

            # --- HUD & Telemetry Overlay ---
            # Title banner
            title_surf = title_font.render("KINETIK // PHASE P1 VISION ENGINE", True, COLOR_CYAN_GLOW)
            screen.blit(title_surf, (30, 25))

            # Camera Status
            cam_color = COLOR_CYAN_GLOW if webcam.is_available else COLOR_HAZARD_RED
            cam_status = f"CAM: {'ACTIVE' if webcam.is_available else 'DISCONNECTED'} ({webcam.fps:.1f} FPS) | Mirror: {webcam.mirror}"
            cam_surf = font.render(cam_status, True, cam_color)
            screen.blit(cam_surf, (30, 60))

            # Tracking Status
            track_color = COLOR_VIOLET_FLUX if hands else (140, 150, 170)
            track_status = f"HANDS DETECTED: {len(hands)}"
            if hands:
                hand_info = " | ".join([f"{h.handedness} ({int(h.confidence * 100)}%)" for h in hands])
                track_status += f" [{hand_info}]"
            track_surf = font.render(track_status, True, track_color)
            screen.blit(track_surf, (30, 85))

            # Performance & Controls Guide
            perf_text = f"APP FPS: {clock.get_fps():.1f} | Frame: {frame_count}"
            perf_surf = status_font.render(perf_text, True, COLOR_HUD_TEXT)
            screen.blit(perf_surf, (30, 115))

            guide_text = "Controls: [M] Toggle Mirror | [C] Toggle Video | [S] Toggle Skeleton | [ESC/Q] Quit"
            guide_surf = status_font.render(guide_text, True, (120, 140, 160))
            screen.blit(guide_surf, (30, DEFAULT_WINDOW_HEIGHT - 35))

            pygame.display.flip()
            clock.tick(TARGET_FPS)
            frame_count += 1

            if max_frames > 0 and frame_count >= max_frames:
                print(f"[KINETIK] Reached requested max_frames={max_frames}, exiting cleanly.")
                running = False

    finally:
        webcam.stop()
        tracker.close()
        pygame.quit()

    return 0


def main():
    parser = argparse.ArgumentParser(description="KINETIK Telekinesis Playground - Phase P1")
    parser.add_argument("--headless", action="store_true", help="Run in headless SDL mode")
    parser.add_argument("--test-frames", type=int, default=0, help="Run for N frames and exit")
    parser.add_argument("--mock-camera", action="store_true", help="Use synthetic mock video generator")
    parser.add_argument("--camera", type=int, default=DEFAULT_CAMERA_INDEX, help="Camera device index")
    args = parser.parse_args()

    return run(
        headless=args.headless,
        max_frames=args.test_frames,
        mock_camera=args.mock_camera,
        camera_index=args.camera
    )


if __name__ == "__main__":
    sys.exit(main())
