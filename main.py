#!/usr/bin/env python3
"""
KINETIK — Webcam-Powered Telekinesis Playground
Application Entry Point with Phase P7 Progression, Unlocks & Local Save
"""
import argparse
import os
import random
import sys

# Auto-detect and forward to local virtual environment if run from global python
if sys.prefix == sys.base_prefix:
    _venv_win = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe")
    _venv_nix = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python")
    _target_py = _venv_win if os.path.exists(_venv_win) else (_venv_nix if os.path.exists(_venv_nix) else None)
    if _target_py and os.path.abspath(sys.executable).lower() != os.path.abspath(_target_py).lower():
        import subprocess
        sys.exit(subprocess.call([_target_py] + sys.argv))

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
from src.game.dual_hand import DualHandSuperpower, DualHandSynthesizer
from src.game.modes import FreePlayMode, GameModeState, ModeType, TargetRushMode
from src.game.ragdoll_mode import RagdollGodMode
from src.game.stack_mode import TheStackMode
from src.game.progression import ProgressionManager
from src.game.scoring import ScoringEngine
from src.gestures.detector import GestureDetector, GestureType
from src.physics.collisions import CollisionEvent
from src.physics.ragdoll import RagdollExpression
from src.physics.slice import KineticBlade
from src.physics.world import PhysicsWorld
from src.rendering.cursor import render_all_cursors
from src.rendering.effects import ScreenShake
from src.rendering.landmarks import render_hand_skeleton
from src.rendering.particles import ParticlePool
from src.rendering.physics_renderer import render_physics_bodies
from src.rendering.ragdoll_renderer import render_contraptions, render_ragdoll
from src.rendering.tether import render_energy_tether
from src.storage.save_manager import SaveManager
from src.ui.hud import render_blade_trails, render_game_hud, render_target_drones


def run(
    headless: bool = False,
    max_frames: int = 0,
    mock_camera: bool = False,
    camera_index: int = DEFAULT_CAMERA_INDEX,
    start_mode: str = "target_rush"
) -> int:
    """Initialize camera, vision, physics, game modes, progression, and Pygame lifecycle."""
    if headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    pygame.init()
    pygame.font.init()

    display_surface = pygame.display.set_mode((DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
    render_surface = pygame.Surface((DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    fonts = {
        "title": pygame.font.SysFont("Consolas", 22, bold=True),
        "big": pygame.font.SysFont("Consolas", 28, bold=True),
        "font": pygame.font.SysFont("Consolas", 18),
        "small": pygame.font.SysFont("Consolas", 14),
        "cursor": pygame.font.SysFont("Consolas", 12, bold=True),
    }

    # Storage & Progression (Phase P7)
    save_manager = SaveManager()
    progression_manager = ProgressionManager(save_manager)

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

    # Phase P3: Physics World
    print("[KINETIK] Initializing Pymunk 2D Physics World...")
    physics_world = PhysicsWorld(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

    # Phase P4: Telekinesis Controller
    print("[KINETIK] Initializing Telekinesis Controller...")
    telekinesis_controller = TelekinesisController(physics_world)

    # Phase 2.0: Dual-Hand Superpower Synthesizer
    print("[KINETIK 2.0] Initializing Dual-Hand Synthesizer (Prop Clash, Vortex, Shield)...")
    dual_hand_synthesizer = DualHandSynthesizer(physics_world)

    # Phase P5: Sensory Juice
    print("[KINETIK] Initializing Particle Pool & Audio Engine...")
    particle_pool = ParticlePool(pool_size=600)
    screen_shake = ScreenShake(max_offset_px=12.0)
    audio_engine = ProceduralAudioEngine()

    # Phase P6 & 2.0: Scoring & Game Modes
    print("[KINETIK] Initializing Scoring Engine & Game Modes...")
    scoring_engine = ScoringEngine()
    ragdoll_mode = RagdollGodMode(physics_world, scoring_engine)
    free_play_mode = FreePlayMode(physics_world, scoring_engine)
    target_rush_mode = TargetRushMode(physics_world, scoring_engine, round_duration_sec=60.0)
    stack_mode = TheStackMode(physics_world, scoring_engine)

    available_modes = [ragdoll_mode, free_play_mode, target_rush_mode, stack_mode]
    if start_mode.lower() == "stack":
        mode_idx = 3
    elif start_mode.lower() == "target_rush":
        mode_idx = 2
    elif start_mode.lower() == "free_play":
        mode_idx = 1
    else:
        mode_idx = 0  # Ragdoll God is the default!

    current_mode = available_modes[mode_idx]
    current_mode.start()
    prev_ragdoll_expr = None
    last_handled_trick = None

    # KINETIK 2.0: Kinetic Blade Slicing Engine
    kinetic_blade = KineticBlade(physics_world.space, telekinesis_controller=telekinesis_controller)
    last_checkpoint_tier_announced = 0

    # Wire collision events for prop impacts
    def on_physics_collision(event: CollisionEvent) -> None:
        particle_pool.emit_burst(
            event.contact_point.x,
            event.contact_point.y,
            count=min(24, int(event.impulse * 0.04) + 6),
            color=COLOR_GOLD_AMBER if event.impulse > 300.0 else COLOR_CYAN_GLOW
        )
        audio_engine.play_impact(event.impulse)
        if event.impulse > 250.0:
            shake_trauma = min(0.6, (event.impulse - 250.0) / 1000.0)
            screen_shake.add_trauma(shake_trauma)

    physics_world.collision_dispatcher.add_listener(on_physics_collision)

    running = True
    frame_count = 0
    show_camera_feed = True
    show_skeleton = True
    round_ended_handled = False

    print(f"[KINETIK] Phase P7 active! Rank: {progression_manager.current_rank.name} | Total XP: {progression_manager.profile.total_xp:,}")

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
                    elif event.key == pygame.K_TAB:
                        mode_idx = (mode_idx + 1) % len(available_modes)
                        current_mode = available_modes[mode_idx]
                        current_mode.start()
                        round_ended_handled = False
                    elif event.key in (pygame.K_r, pygame.K_SPACE) and current_mode.state == GameModeState.ROUND_OVER:
                        current_mode.start()
                        round_ended_handled = False
                    elif event.key == pygame.K_SPACE:
                        primary = gesture_detector.get_primary_hand(active_gesture_states if 'active_gesture_states' in locals() else [])
                        sx = primary.screen_pos[0] if primary else random.uniform(200, DEFAULT_WINDOW_WIDTH - 200)
                        sy = primary.screen_pos[1] if primary else 120.0
                        physics_world.spawn_sphere(sx, sy, radius=random.uniform(22, 34))
                    elif event.key == pygame.K_b:
                        bx = random.uniform(200, DEFAULT_WINDOW_WIDTH - 200)
                        physics_world.spawn_box(bx, 120.0, size=random.uniform(40, 56))
                    elif event.key == pygame.K_r:
                        current_mode.reset()
                        round_ended_handled = False
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

            # Audio triggers & Achievements on gesture state changes
            for state in active_gesture_states:
                if state.just_pinched:
                    audio_engine.play_grab()
                elif state.just_released and state.speed > 300.0:
                    audio_engine.play_throw(state.speed)
                    scoring_engine.register_throw()
                    progression_manager.unlock_achievement("ACH_FIRST_FLING")
                    if state.speed >= 1800.0:
                        progression_manager.unlock_achievement("ACH_MACH_FLING")
                elif state.gesture_type == GestureType.PUSH:
                    audio_engine.play_push()
                    screen_shake.add_trauma(0.2)
                    particle_pool.emit_burst(state.screen_pos[0], state.screen_pos[1], count=14, color=COLOR_HAZARD_RED)

            # 4. Telekinesis Controller Update
            telekinesis_controller.update(active_gesture_states, now=frame_ts)

            # 4b. Dual-Hand Combos & Superpowers
            dual_events = dual_hand_synthesizer.process_dual_hands(
                active_gesture_states,
                active_holds=telekinesis_controller.get_active_holds(),
                now=frame_ts
            )
            for dev in dual_events:
                screen_shake.add_trauma(dev.screen_shake_trauma)
                if dev.power_type == DualHandSuperpower.PROP_CLASH:
                    audio_engine.play_clash()
                    particle_pool.emit_clash_nova(dev.position[0], dev.position[1])
                    scoring_engine.register_hit(dev.bonus_score, 1400.0, dev.position, COLOR_GOLD_AMBER)
                elif dev.power_type == DualHandSuperpower.SINGULARITY_RIFT:
                    audio_engine.play_vortex()
                    scoring_engine.register_hit(dev.bonus_score, 700.0, dev.position, COLOR_VIOLET_FLUX)
                elif dev.power_type == DualHandSuperpower.DUAL_TIDAL_WAVE:
                    audio_engine.play_push()
                    particle_pool.emit_clash_nova(dev.position[0], dev.position[1])

            # 4c. KINETIK 2.0: Kinetic Blade Gesture Slicing
            kinetic_blade.update_trails(dt)
            for state in active_gesture_states:
                cuts = kinetic_blade.process_hand_slicing(state, dt, now=frame_ts)
                for cut in cuts:
                    screen_shake.add_trauma(0.35 if cut.sliced_target else 0.22)
                    audio_engine.play_slice()
                    particle_pool.emit_slice_sparks(cut.cut_point[0], cut.cut_point[1])
                    scoring_engine.register_hit(cut.bonus_score, 1200.0, cut.cut_point, COLOR_WHITE_BRIGHT)
                    progression_manager.unlock_achievement("ACH_CYBER_SLICE")

            # Check Stack Mode checkpoint chime
            if isinstance(current_mode, TheStackMode) and current_mode.recent_checkpoint_event:
                if current_mode.recent_checkpoint_event.tier != last_checkpoint_tier_announced:
                    last_checkpoint_tier_announced = current_mode.recent_checkpoint_event.tier
                    audio_engine.play_chime()
                    screen_shake.add_trauma(0.25)
                    particle_pool.emit_burst(DEFAULT_WINDOW_WIDTH * 0.5, 200.0, count=36, color=COLOR_GOLD_AMBER)

            # Ragdoll comedic voice and contraption audio
            if isinstance(current_mode, RagdollGodMode) and current_mode.ragdoll:
                rag = current_mode.ragdoll
                if rag.expression == RagdollExpression.PANIC_SCREAM and prev_ragdoll_expr != RagdollExpression.PANIC_SCREAM:
                    audio_engine.play_screeeam()
                elif rag.expression == RagdollExpression.DIZZY and prev_ragdoll_expr != RagdollExpression.DIZZY:
                    audio_engine.play_oof()
                    screen_shake.add_trauma(0.3)
                prev_ragdoll_expr = rag.expression

                if current_mode.recent_trick and current_mode.recent_trick != last_handled_trick:
                    last_handled_trick = current_mode.recent_trick
                    if "BUMPER" in current_mode.recent_trick.name:
                        audio_engine.play_bumper_ping()
                        screen_shake.add_trauma(0.25)
                    elif "TRAMPOLINE" in current_mode.recent_trick.name:
                        audio_engine.play_boing()
                        screen_shake.add_trauma(0.2)
                    elif "PORTAL" in current_mode.recent_trick.name:
                        audio_engine.play_portal_warp()

            # 5. Game Mode & Scoring Update
            current_mode.update(dt)
            scoring_engine.update(dt)

            # Record round score when round ends
            if current_mode.state == GameModeState.ROUND_OVER and not round_ended_handled:
                round_ended_handled = True
                progression_manager.record_round_results(
                    final_score=scoring_engine.score,
                    total_hits=scoring_engine.total_hits,
                    max_combo=scoring_engine.max_combo
                )

            # 6. Physics Simulation Step
            physics_world.step(dt)

            # 7. Particles & Screen-Shake Update
            active_particles = particle_pool.update(dt)
            shake_x, shake_y = screen_shake.update(dt)

            for body in physics_world.get_dynamic_bodies():
                if body.velocity.length > 400.0:
                    particle_pool.emit_trail(body.position.x, body.position.y, color=COLOR_CYAN_GLOW)

            # --- Presentation Rendering ---
            render_surface.fill(COLOR_BACKGROUND)

            # Draw camera feed
            if show_camera_feed and frame_bgr is not None:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                frame_surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                frame_surf = pygame.transform.scale(frame_surf, (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
                frame_surf.set_alpha(140)
                render_surface.blit(frame_surf, (0, 0))

            # Draw target drones if in Target Rush
            if isinstance(current_mode, TargetRushMode):
                render_target_drones(render_surface, current_mode.targets)

            # Draw Ragdoll contraptions and character
            if isinstance(current_mode, RagdollGodMode):
                render_contraptions(
                    render_surface,
                    current_mode.bumpers,
                    current_mode.portals,
                    current_mode.trampoline,
                    now=frame_ts
                )
                if current_mode.ragdoll:
                    render_ragdoll(render_surface, current_mode.ragdoll)

            # Check targeted body near hand cursor
            targeted_body = None
            if primary_hand:
                targeted_body, _ = telekinesis_controller.find_nearest_body(primary_hand.screen_pos)

            # Draw physics bodies
            dynamic_bodies = physics_world.get_dynamic_bodies()
            render_physics_bodies(render_surface, dynamic_bodies, targeted_body=targeted_body)

            # Draw energy tethers
            active_holds = telekinesis_controller.get_active_holds()
            for hand_pos, body, _ in active_holds:
                render_energy_tether(
                    render_surface,
                    hand_pos=hand_pos,
                    body_pos=(body.position.x, body.position.y),
                    color=COLOR_CYAN_GLOW
                )

            # Draw Singularity Vortex & Suction Motes
            if dual_hand_synthesizer.active_singularity:
                dual_hand_synthesizer.active_singularity.draw(render_surface)
                particle_pool.emit_singularity_motes(
                    dual_hand_synthesizer.active_singularity.center[0],
                    dual_hand_synthesizer.active_singularity.center[1]
                )

            # Draw Kinetic Forcefield Shield
            dual_hand_synthesizer.shield.draw(render_surface)

            # Draw Kinetic Blade laser trails
            render_blade_trails(render_surface, kinetic_blade.active_trails)

            # Draw particles
            particle_pool.draw(render_surface)

            # Draw hand skeleton overlay
            if show_skeleton and hands:
                render_hand_skeleton(
                    render_surface,
                    hands,
                    DEFAULT_WINDOW_WIDTH,
                    DEFAULT_WINDOW_HEIGHT,
                    primary_color=COLOR_CYAN_GLOW
                )

            # Draw gesture cursors
            render_all_cursors(render_surface, active_gesture_states, fonts["cursor"])

            # Draw HUD (Score, Timer, Rank, Popups, Guidance)
            render_game_hud(
                render_surface,
                current_mode,
                scoring_engine,
                progression_manager,
                primary_hand,
                targeted_body,
                bool(active_holds),
                fonts,
                DEFAULT_WINDOW_WIDTH,
                DEFAULT_WINDOW_HEIGHT
            )

            guide_text = "[TAB] Mode | Grab & Fling Buddy | [SPACE] Spawn | [R] Reset | [M] Mute | [ESC] Quit"
            render_surface.blit(fonts["small"].render(guide_text, True, (130, 160, 180)), (30, DEFAULT_WINDOW_HEIGHT - 35))

            # Blit with screen shake
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
    parser = argparse.ArgumentParser(description="KINETIK Telekinesis Playground - Phase P7")
    parser.add_argument("--headless", action="store_true", help="Run in headless SDL mode")
    parser.add_argument("--test-frames", type=int, default=0, help="Run for N frames and exit")
    parser.add_argument("--mock-camera", action="store_true", help="Use synthetic mock video generator")
    parser.add_argument("--camera", type=int, default=DEFAULT_CAMERA_INDEX, help="Camera device index")
    parser.add_argument("--mode", type=str, default="ragdoll", choices=["ragdoll", "target_rush", "free_play", "stack"], help="Game mode")
    args = parser.parse_args()

    return run(
        headless=args.headless,
        max_frames=args.test_frames,
        mock_camera=args.mock_camera,
        camera_index=args.camera,
        start_mode=args.mode
    )


if __name__ == "__main__":
    sys.exit(main())
