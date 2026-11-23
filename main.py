#!/usr/bin/env python3
"""
KINETIK — Webcam-Powered Telekinesis Playground
Application Entry Point with Phase P4 Telekinetic Interaction Loop
"""
import argparse
import os
import random
import sys
import cv2
import pygame

from src.camera.hand_tracker import HandTracker
from src.camera.webcam import WebcamCapture
from src.config import (
    COLOR_BACKGROUND,
    COLOR_CYAN_GLOW,
    COLOR_GOLD_AMBER,
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
from src.game.controller import TelekinesisController
from src.gestures.detector import GestureDetector
from src.physics.world import PhysicsWorld
from src.rendering.cursor import render_all_cursors
from src.rendering.landmarks import render_hand_skeleton
from src.rendering.physics_renderer import render_physics_bodies
from src.rendering.tether import render_energy_tether


def run(
    headless: bool = False,
    max_frames: int = 0,
    mock_camera: bool = False,
    camera_index: int = DEFAULT_CAMERA_INDEX
) -> int:
    """Initialize full telekinetic vision, physics, and Pygame lifecycle."""
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

    # Phase P2: Gesture Engine
    print("[KINETIK] Initializing Gesture Engine...")
    gesture_detector = GestureDetector(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

    # Phase P3: Physics World Playground
    print("[KINETIK] Initializing Pymunk 2D Physics World...")
    physics_world = PhysicsWorld(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
    physics_world.reset_default_playground()

    # Phase P4: Telekinesis Interaction Controller
    print("[KINETIK] Initializing Telekinesis Controller (Soft Springs & Fling)...")
    telekinesis_controller = TelekinesisController(physics_world)

    running = True
    frame_count = 0
    show_camera_feed = True
    show_skeleton = True

    print("[KINETIK] Phase P4 active! Pinch near objects to GRAB, flick to THROW, open palm thrust to PUSH!")

    try:
        while running:
            raw_dt = clock.get_time() / 1000.0
            dt = min(raw_dt, 0.1) if raw_dt > 0 else 1.0 / TARGET_FPS

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_SPACE:
                        primary = gesture_detector.get_primary_hand(active_gesture_states if 'active_gesture_states' in locals() else [])
                        sx = primary.screen_pos[0] if primary else random.uniform(200, DEFAULT_WINDOW_WIDTH - 200)
                        sy = primary.screen_pos[1] if primary else 120.0
                        physics_world.spawn_sphere(sx, sy, radius=random.uniform(22, 34))
                    elif event.key == pygame.K_b:
                        bx = random.uniform(200, DEFAULT_WINDOW_WIDTH - 200)
                        physics_world.spawn_box(bx, 120.0, size=random.uniform(40, 56))
                    elif event.key == pygame.K_r:
                        physics_world.reset_default_playground()
                    elif event.key == pygame.K_g:
                        physics_world.toggle_zero_gravity()
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

            # 3. Gesture Recognition
            active_gesture_states = gesture_detector.process_hands(hands, now=frame_ts)
            primary_hand = gesture_detector.get_primary_hand(active_gesture_states)

            # 4. Telekinesis Controller Update (Grab, Hold, Throw, Push)
            telekinesis_controller.update(active_gesture_states, now=frame_ts)

            # 5. Physics Simulation Step
            physics_world.step(dt)

            # --- Presentation Rendering ---
            screen.fill(COLOR_BACKGROUND)

            # Draw camera feed
            if show_camera_feed and frame_bgr is not None:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                frame_surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                frame_surf = pygame.transform.scale(frame_surf, (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
                frame_surf.set_alpha(150)
                screen.blit(frame_surf, (0, 0))

            # Draw physics bodies
            dynamic_bodies = physics_world.get_dynamic_bodies()
            render_physics_bodies(screen, dynamic_bodies)

            # Draw telekinetic energy tethers for active holds
            active_holds = telekinesis_controller.get_active_holds()
            for hand_pos, body, _ in active_holds:
                render_energy_tether(
                    screen,
                    hand_pos=hand_pos,
                    body_pos=(body.position.x, body.position.y),
                    color=COLOR_CYAN_GLOW
                )

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
            render_all_cursors(screen, active_gesture_states, cursor_font)

            # --- HUD & Telemetry Overlay ---
            title_surf = title_font.render("KINETIK // PHASE P4 TELEKINESIS CORE", True, COLOR_CYAN_GLOW)
            screen.blit(title_surf, (30, 25))

            # Telekinesis State
            holding_info = f"HOLDING ({len(active_holds)} objs)" if active_holds else "READY TO GRAB"
            telem_color = COLOR_GOLD_AMBER if active_holds else COLOR_CYAN_GLOW
            status_text = (
                f"STATUS: {holding_info} | "
                f"PROPS: {len(dynamic_bodies)} | "
                f"CAM: {'ACTIVE' if webcam.is_available else 'MOCK/OFF'}"
            )
            status_surf = font.render(status_text, True, telem_color)
            screen.blit(status_surf, (30, 60))

            # Gesture Telemetry
            if primary_hand:
                hand_telem = (
                    f"GESTURE: {primary_hand.gesture_type.name} | "
                    f"PINCH: {int(primary_hand.pinch_factor * 100)}% | "
                    f"SPEED: {int(primary_hand.speed)} px/s"
                )
            else:
                hand_telem = "GESTURE: NO HAND (Wave hand in front of camera)"

            telem_surf = font.render(hand_telem, True, COLOR_HUD_TEXT)
            screen.blit(telem_surf, (30, 85))

            # Performance stats
            perf_text = f"APP FPS: {clock.get_fps():.1f} | Frame: {frame_count}"
            perf_surf = status_font.render(perf_text, True, COLOR_HUD_TEXT)
            screen.blit(perf_surf, (30, 115))

            guide_text = "Pinch near an object to GRAB | Flick hand to THROW | Open-palm thrust to PUSH | [SPACE] Spawn | [R] Reset | [ESC] Quit"
            guide_surf = status_font.render(guide_text, True, (140, 170, 190))
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
    parser = argparse.ArgumentParser(description="KINETIK Telekinesis Playground - Phase P4")
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
