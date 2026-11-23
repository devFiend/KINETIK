#!/usr/bin/env python3
"""
KINETIK — Webcam-Powered Telekinesis Playground
Application Entry Point with Phase P5 Sensory Juice (Particles, Screen-Shake, Procedural Audio)
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
from src.game.audio import ProceduralAudioEngine
from src.game.controller import TelekinesisController
from src.gestures.detector import GestureDetector, GestureType
from src.physics.collisions import CollisionEvent
from src.physics.world import PhysicsWorld
from src.rendering.cursor import render_all_cursors
from src.rendering.effects import ScreenShake
from src.rendering.landmarks import render_hand_skeleton
from src.rendering.particles import ParticlePool
from src.rendering.physics_renderer import render_physics_bodies
from src.rendering.tether import render_energy_tether


def run(
    headless: bool = False,
    max_frames: int = 0,
    mock_camera: bool = False,
    camera_index: int = DEFAULT_CAMERA_INDEX
) -> int:
    """Initialize full sensory telekinetic vision, physics, particles, audio, and Pygame lifecycle."""
    if headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    pygame.init()
    pygame.font.init()

    # Offscreen render surface for screen-shake compositing
    display_surface = pygame.display.set_mode((DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
    render_surface = pygame.Surface((DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
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
    print("[KINETIK] Initializing Telekinesis Controller...")
    telekinesis_controller = TelekinesisController(physics_world)

    # Phase P5: Sensory Juice (Particles, Audio & Screen Shake)
    print("[KINETIK] Initializing Particle Pool, Audio Engine & Screen Shake...")
    particle_pool = ParticlePool(pool_size=600)
    screen_shake = ScreenShake(max_offset_px=12.0)
    audio_engine = ProceduralAudioEngine()

    # Wire collision events to particles, audio, and screen shake!
    def on_physics_collision(event: CollisionEvent) -> None:
        # Spawn impact shrapnel burst
        particle_pool.emit_burst(
            event.contact_point.x,
            event.contact_point.y,
            count=min(24, int(event.impulse * 0.04) + 6),
            color=COLOR_GOLD_AMBER if event.impulse > 300.0 else COLOR_CYAN_GLOW
        )
        # Play impact sound scaled by impulse
        audio_engine.play_impact(event.impulse)

        # Trigger screen shake on heavy impacts
        if event.impulse > 250.0:
            shake_trauma = min(0.6, (event.impulse - 250.0) / 1000.0)
            screen_shake.add_trauma(shake_trauma)

    physics_world.collision_dispatcher.add_listener(on_physics_collision)

    running = True
    frame_count = 0
    show_camera_feed = True
    show_skeleton = True

    print("[KINETIK] Phase P5 Sensory Engine active! Controls: [SPACE] Ball | [B] Box | [R] Reset | [G] Zero-G | [M] Mute | [ESC] Quit")

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
                        screen_shake.add_trauma(0.3)
                    elif event.key == pygame.K_g:
                        physics_world.toggle_zero_gravity()
                    elif event.key == pygame.K_m:
                        audio_engine.toggle_mute()
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

            # Audio triggers on gesture state changes
            for state in active_gesture_states:
                if state.just_pinched:
                    audio_engine.play_grab()
                elif state.just_released and state.speed > 300.0:
                    audio_engine.play_throw(state.speed)
                elif state.gesture_type == GestureType.PUSH:
                    audio_engine.play_push()
                    screen_shake.add_trauma(0.2)
                    particle_pool.emit_burst(state.screen_pos[0], state.screen_pos[1], count=14, color=COLOR_HAZARD_RED)

            # 4. Telekinesis Controller Update
            telekinesis_controller.update(active_gesture_states, now=frame_ts)

            # 5. Physics Simulation Step
            physics_world.step(dt)

            # 6. Particles & Screen-Shake Update
            active_particles = particle_pool.update(dt)
            shake_x, shake_y = screen_shake.update(dt)

            # Emit motion trail particles behind high-speed objects
            for body in physics_world.get_dynamic_bodies():
                speed = body.velocity.length
                if speed > 400.0:
                    particle_pool.emit_trail(body.position.x, body.position.y, color=COLOR_CYAN_GLOW)

            # --- Presentation Rendering onto render_surface ---
            render_surface.fill(COLOR_BACKGROUND)

            # Draw camera feed
            if show_camera_feed and frame_bgr is not None:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                frame_surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                frame_surf = pygame.transform.scale(frame_surf, (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
                frame_surf.set_alpha(150)
                render_surface.blit(frame_surf, (0, 0))

            # Draw physics bodies
            dynamic_bodies = physics_world.get_dynamic_bodies()
            render_physics_bodies(render_surface, dynamic_bodies)

            # Draw telekinetic energy tethers for active holds
            active_holds = telekinesis_controller.get_active_holds()
            for hand_pos, body, _ in active_holds:
                render_energy_tether(
                    render_surface,
                    hand_pos=hand_pos,
                    body_pos=(body.position.x, body.position.y),
                    color=COLOR_CYAN_GLOW
                )

            # Draw active particles
            particle_pool.draw(render_surface)

            # Draw skeleton overlay
            if show_skeleton and hands:
                render_hand_skeleton(
                    render_surface,
                    hands,
                    DEFAULT_WINDOW_WIDTH,
                    DEFAULT_WINDOW_HEIGHT,
                    primary_color=COLOR_CYAN_GLOW
                )

            # Draw telekinetic targeting reticles and gesture cursors
            render_all_cursors(render_surface, active_gesture_states, cursor_font)

            # --- HUD & Telemetry Overlay ---
            title_surf = title_font.render("KINETIK // PHASE P5 SENSORY JUICE", True, COLOR_CYAN_GLOW)
            render_surface.blit(title_surf, (30, 25))

            # Telemetry Status
            audio_status = "MUTED" if audio_engine.muted else "AUDIO ON"
            status_text = (
                f"HOLDS: {len(active_holds)} | "
                f"PARTICLES: {active_particles} | "
                f"TRAUMA: {screen_shake.trauma:.2f} | "
                f"{audio_status}"
            )
            render_surface.blit(font.render(status_text, True, COLOR_CYAN_GLOW), (30, 60))

            if primary_hand:
                hand_telem = (
                    f"GESTURE: {primary_hand.gesture_type.name} | "
                    f"PINCH: {int(primary_hand.pinch_factor * 100)}% | "
                    f"SPEED: {int(primary_hand.speed)} px/s"
                )
            else:
                hand_telem = "GESTURE: NO HAND (Wave hand in front of camera)"

            render_surface.blit(font.render(hand_telem, True, COLOR_HUD_TEXT), (30, 85))

            perf_text = f"APP FPS: {clock.get_fps():.1f} | Frame: {frame_count}"
            render_surface.blit(status_font.render(perf_text, True, COLOR_HUD_TEXT), (30, 115))

            guide_text = "Flick to THROW | Palm thrust to PUSH | [SPACE] Spawn | [B] Box | [R] Reset | [G] Zero-G | [M] Mute | [ESC] Quit"
            render_surface.blit(status_font.render(guide_text, True, (140, 170, 190)), (30, DEFAULT_WINDOW_HEIGHT - 35))

            # Blit render_surface to display with screen-shake offset
            display_surface.fill((0, 0, 0))
            display_surface.blit(render_surface, (shake_x, shake_y))

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
    parser = argparse.ArgumentParser(description="KINETIK Telekinesis Playground - Phase P5")
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
