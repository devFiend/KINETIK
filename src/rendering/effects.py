"""Camera screen-shake trauma model and visual juice effects."""
import random
from typing import Tuple


class ScreenShake:
    """
    Trauma-based screen shake model.
    Trauma is in range [0.0, 1.0].
    Offset = (trauma ^ 2) * max_offset.
    Decays smoothly over time.
    """

    def __init__(self, max_offset_px: float = 14.0, decay_rate: float = 2.2):
        self.max_offset = max_offset_px
        self.decay_rate = decay_rate
        self.trauma: float = 0.0

    def add_trauma(self, amount: float) -> None:
        """Add trauma energy, clamped to [0.0, 1.0]."""
        self.trauma = min(1.0, self.trauma + max(0.0, amount))

    def update(self, dt: float) -> Tuple[int, int]:
        """
        Advance decay and return (offset_x, offset_y) pixel displacements.
        """
        if self.trauma <= 0.0:
            return 0, 0

        self.trauma = max(0.0, self.trauma - self.decay_rate * dt)
        intensity = self.trauma * self.trauma  # Non-linear quadratic shake

        offset_x = int(random.uniform(-1.0, 1.0) * self.max_offset * intensity)
        offset_y = int(random.uniform(-1.0, 1.0) * self.max_offset * intensity)
        return offset_x, offset_y
