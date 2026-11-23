"""Global configuration, constants, color themes, and tuning parameters for KINETIK."""
from dataclasses import dataclass
from typing import Tuple

# Display & Engine Settings
WINDOW_TITLE: str = "KINETIK — Webcam Telekinesis Playground"
DEFAULT_WINDOW_WIDTH: int = 1280
DEFAULT_WINDOW_HEIGHT: int = 720
TARGET_FPS: int = 60
FIXED_PHYSICS_DT: float = 1.0 / 60.0

# Camera Ingestion Defaults
DEFAULT_CAMERA_INDEX: int = 0
DEFAULT_CAM_WIDTH: int = 640
DEFAULT_CAM_HEIGHT: int = 480
DEFAULT_MIRROR_MODE: bool = True

# Gesture & Telekinesis Tuning
# Calibrated for natural webcam distances (0.5m - 1.2m)
PINCH_ENTER_THRESHOLD: float = 0.080  # Distance between thumb & index tip to enter pinch (more forgiving)
PINCH_EXIT_THRESHOLD: float = 0.120   # Distance to exit pinch (hysteresis to prevent accidental drop)
PINCH_DEBOUNCE_FRAMES: int = 2        # Consecutive frames required to confirm state change
SELECTION_RADIUS_PX: float = 240.0    # Expanded reach radius so player can grab balls from desk/floor
VELOCITY_HISTORY_FRAMES: int = 5      # Rolling window size for throw velocity calculation
MAX_RELEASE_VELOCITY: float = 2500.0  # Velocity clamp to prevent boundary tunneling (px/s)
THROW_FORCE_MULTIPLIER: float = 1.5   # Dynamic fling boost multiplier
TRACKING_LOSS_GRACE_MS: int = 400     # Grace period before dropping held object on tracking dropout

# Physics Simulation Defaults
DEFAULT_GRAVITY_Y: float = 800.0      # Downward gravitational acceleration (px/s^2)
SPRING_STIFFNESS: float = 480.0       # Snappy, tactile telekinetic tether spring stiffness (N/m)
SPRING_DAMPING: float = 35.0          # Spring damping coefficient (N*s/m)

# Cyberpunk / Control-Room Color Palette (RGB)
COLOR_BACKGROUND: Tuple[int, int, int] = (11, 13, 19)       # Deep Obsidian
COLOR_CYAN_GLOW: Tuple[int, int, int] = (0, 240, 255)       # Neon Electric Cyan
COLOR_VIOLET_FLUX: Tuple[int, int, int] = (157, 0, 255)     # Radiant Violet
COLOR_GOLD_AMBER: Tuple[int, int, int] = (255, 184, 0)      # High-voltage Amber
COLOR_WHITE_BRIGHT: Tuple[int, int, int] = (245, 245, 250)  # Pure Bright White
COLOR_HUD_TEXT: Tuple[int, int, int] = (180, 210, 230)      # Soft Telemetry Blue
COLOR_HAZARD_RED: Tuple[int, int, int] = (255, 50, 75)      # Critical Hazard Red


@dataclass
class EngineConfig:
    """Runtime engine configuration."""
    window_width: int = DEFAULT_WINDOW_WIDTH
    window_height: int = DEFAULT_WINDOW_HEIGHT
    fps: int = TARGET_FPS
    cam_index: int = DEFAULT_CAMERA_INDEX
    mirror_camera: bool = DEFAULT_MIRROR_MODE
    debug_overlay: bool = True
    reduced_motion: bool = False
