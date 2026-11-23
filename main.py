#!/usr/bin/env python3
"""
KINETIK — Webcam-Powered Telekinesis Playground
Application Entry Point with Phase P2 Input Processing & Gesture Engine
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
from src.gestures.detector import GestureDetector
from src.rendering.cursor import render_all_cursors
from src.rendering.landmarks import render_hand_skeleton


def run(
    headless: bool = False,
    max_frames: int = 0,
    mock_camera: bool = False,
    camera_index: int = DEFAULT_CAMERA_INDEX
) -> int:
    """Initialize camera, vision engine, gesture recognizer, and Pygame lifecycle."""
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
    cursor_font = pygame.font.SysFont("Consolas", 12, bold=True)

    # Phase P1: Vision Pipeline
    print(f"[KINETIK] Initializing webcam capture on index={camera_index}...")
    webcam = WebcamCapture(
        camera_index=camera_index,
        width=DEFAULT_CAM_WIDTH,
        height=DEFAULT_CAM_HEIGHT,
        mirror=DEFAULT_MIRROR_MODE,
        mock_mode=mock_camera
    )
    webcam.start()

    print("[KINETIK] Initializing MediaPipe HandTracker...")
    tracker = HandTracker()

    # Phase P2: Input Processing & Gesture Engine
    print("[KINETIK] Initializing Gesture Engine (Hysteresis & Adaptive Smoothing)...")
    gesture_detector = GestureDetector(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

    running = True
    frame_count = 0
    show_camera_feed = True
    show_skeleton = True

    print("[KINETIK] Phase P2 active. Controls: [M]irror, [C]amera toggle, [S]keleton, [ESC/Q]uit")

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
                    elif event.key == pygame.K_c:
                        show_camera_feed = not show_camera_feed
                    elif event.key == pygame.K_s:
                        show_skeleton = not show_skeleton

            # 1. Video Ingestion
            frame_bgr, frame_ts = webcam.get_latest_frame()
            hands = []

            # 2. Vision Inference
            if frame_bgr is not None:
                hands = tracker.process_frame(frame_bgr)

            # 3. Gesture Recognition & Coordinate Smoothing
            gesture_states = gesture_detector.process_hands(hands, now=frame_ts)
            primary_hand = gesture_detector.get_primary_hand(gesture_states)

            # --- Presentation Rendering ---
            screen.fill(COLOR_BACKGROUND)

            # Draw camera feed
            if show_camera_feed and frame_bgr is not None:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                frame_surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                frame_surf = pygame.transform.scale(frame_surf, (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
                frame_surf.set_alpha(170)
                screen.blit(frame_surf, (0, 0))

            # Draw skeleton overlay
            if show_skeleton and hands:
                render_hand_skeleton(
                    screen,
                    hands,
                    DEFAULT_WINDOW_WIDTH,
                    DEFAULT_WINDOW_HEIGHT,
                    primary_color=COLOR_CYAN_GLOW
                )

            # Draw telekinetic targeting reticles and gesture cursors
            render_all_cursors(screen, gesture_states, cursor_font)

            # --- HUD & Telemetry Overlay ---
            title_surf = title_font.render("KINETIK // PHASE P2 GESTURE ENGINE", True, COLOR_CYAN_GLOW)
            screen.blit(title_surf, (30, 25))

            # Camera Status
            cam_color = COLOR_CYAN_GLOW if webcam.is_available else COLOR_HAZARD_RED
            cam_status = f"CAM: {'ACTIVE' if webcam.is_available else 'DISCONNECTED'} ({webcam.fps:.1f} FPS) | Mirror: {webcam.mirror}"
            cam_surf = font.render(cam_status, True, cam_color)
            screen.blit(cam_surf, (30, 60))

            # Gesture Telemetry
            if primary_hand:
                telemetry_color = COLOR_WHITE_BRIGHT if primary_hand.is_pinched else COLOR_CYAN_GLOW
                telemetry_text = (
                    f"GESTURE: {primary_hand.gesture_type.name} | "
                    f"PINCH DIST: {primary_hand.pinch_distance:.3f} | "
                    f"FACTOR: {int(primary_hand.pinch_factor * 100)}% | "
                    f"SPEED: {int(primary_hand.speed)} px/s"
                )
            else:
                telemetry_color = (130, 140, 160)
                telemetry_text = "GESTURE: NO HAND DETECTED (Wave hand in front of camera)"

            telem_surf = font.render(telemetry_text, True, telemetry_color)
            screen.blit(telem_surf, (30, 85))

            # Performance stats
            perf_text = f"APP FPS: {clock.get_fps():.1f} | Frame: {frame_count}"
            perf_surf = status_font.render(perf_text, True, COLOR_HUD_TEXT)
            screen.blit(perf_surf, (30, 115))

            guide_text = "Controls: Pinch Thumb+Index to Grab | Flick Hand to Throw | [M]irror | [C]amera | [S]keleton | [ESC] Quit"
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
    parser = argparse.ArgumentParser(description="KINETIK Telekinesis Playground - Phase P2")
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
