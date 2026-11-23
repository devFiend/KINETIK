"""Adaptive smoothing filters and rolling-window velocity estimation."""
from collections import deque
import math
import time
from typing import Deque, List, Optional, Tuple
import numpy as np

from src.config import MAX_RELEASE_VELOCITY, VELOCITY_HISTORY_FRAMES


class AdaptiveEMASmoother2D:
    """
    Adaptive Exponential Moving Average (EMA) 2D coordinate filter.
    Dynamically adjusts alpha between alpha_min and alpha_max based on speed.
    - Low speed (aiming/holding): low alpha -> heavy smoothing, zero sensor jitter.
    - High speed (flicking/throwing): high alpha -> instant responsiveness, minimal lag.
    """

    def __init__(
        self,
        alpha_min: float = 0.25,
        alpha_max: float = 0.85,
        speed_threshold_px: float = 800.0
    ):
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        self.speed_threshold = speed_threshold_px

        self._current: Optional[Tuple[float, float]] = None
        self._last_time: float = 0.0

    def reset(self) -> None:
        """Reset internal filter state."""
        self._current = None
        self._last_time = 0.0

    def filter(self, x: float, y: float, timestamp: Optional[float] = None) -> Tuple[float, float]:
        """Apply adaptive smoothing to input coordinates."""
        now = timestamp if timestamp is not None else time.time()

        if self._current is None:
            self._current = (float(x), float(y))
            self._last_time = now
            return self._current

        dt = max(1e-4, now - self._last_time)
        dx = x - self._current[0]
        dy = y - self._current[1]
        distance = math.hypot(dx, dy)
        speed = distance / dt

        # Dynamically scale alpha
        speed_factor = min(1.0, speed / self.speed_threshold)
        alpha = self.alpha_min + (self.alpha_max - self.alpha_min) * speed_factor

        smoothed_x = alpha * x + (1.0 - alpha) * self._current[0]
        smoothed_y = alpha * y + (1.0 - alpha) * self._current[1]

        self._current = (smoothed_x, smoothed_y)
        self._last_time = now
        return self._current


class RollingVelocityEstimator:
    """
    Computes velocity vectors from a rolling history buffer using weighted backward differences.
    Clamps maximum velocity to prevent physics boundary tunneling.
    """

    def __init__(
        self,
        history_size: int = VELOCITY_HISTORY_FRAMES,
        max_velocity: float = MAX_RELEASE_VELOCITY
    ):
        self.history_size = max(2, history_size)
        self.max_velocity = max_velocity
        self._buffer: Deque[Tuple[float, float, float]] = deque(maxlen=self.history_size)  # (x, y, timestamp)

    def reset(self) -> None:
        """Clear rolling buffer."""
        self._buffer.clear()

    def add_sample(self, x: float, y: float, timestamp: Optional[float] = None) -> None:
        """Add a position coordinate with timestamp to the rolling buffer."""
        now = timestamp if timestamp is not None else time.time()
        self._buffer.append((float(x), float(y), now))

    def get_velocity(self) -> Tuple[float, float, float]:
        """
        Calculate weighted release velocity vector (vx, vy) and magnitude.
        Returns:
            (vx_clamped, vy_clamped, speed_clamped)
        """
        if len(self._buffer) < 2:
            return 0.0, 0.0, 0.0

        samples = list(self._buffer)
        n = len(samples) - 1

        # Calculate finite backward differences
        vx_sum = 0.0
        vy_sum = 0.0
        weight_sum = 0.0

        for i in range(n):
            x1, y1, t1 = samples[i]
            x2, y2, t2 = samples[i + 1]
            dt = max(1e-4, t2 - t1)

            # Linear recency weighting: more recent frames have higher weight
            weight = float(i + 1)
            vx_sum += ((x2 - x1) / dt) * weight
            vy_sum += ((y2 - y1) / dt) * weight
            weight_sum += weight

        if weight_sum <= 0:
            return 0.0, 0.0, 0.0

        vx = vx_sum / weight_sum
        vy = vy_sum / weight_sum
        speed = math.hypot(vx, vy)

        # Enforce velocity clamping
        if speed > self.max_velocity and speed > 0:
            scale = self.max_velocity / speed
            vx *= scale
            vy *= scale
            speed = self.max_velocity

        return vx, vy, speed
