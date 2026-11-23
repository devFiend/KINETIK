"""Scoring calculations, combo multipliers, decay timers, and floating score popups."""
import time
from typing import List, Tuple

# Multiplier step tiers
COMBO_TIERS: List[float] = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
COMBO_DECAY_WINDOW_SEC: float = 3.5  # Seconds before combo decays 1 tier


class FloatingScore:
    """Floating animated score indicator rising and fading."""

    def __init__(self, x: float, y: float, points: int, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.points = points
        self.color = color
        self.life = 0.8
        self.max_life = 0.8

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.y -= 45.0 * dt  # Float upwards
        return self.life > 0.0


class ScoringEngine:
    """
    Manages score accumulation, combo multiplier progression, and streak decay timing.
    """

    def __init__(self):
        self.score: int = 0
        self.total_hits: int = 0
        self.total_throws: int = 0
        self.combo_tier_idx: int = 0
        self.max_combo: float = 1.0
        self.combo_timer: float = 0.0
        self.floating_scores: List[FloatingScore] = []

    @property
    def combo_multiplier(self) -> float:
        return COMBO_TIERS[self.combo_tier_idx]

    @property
    def combo_decay_fraction(self) -> float:
        """Normalized remaining combo time [0.0, 1.0]."""
        if self.combo_tier_idx == 0:
            return 0.0
        return max(0.0, min(1.0, self.combo_timer / COMBO_DECAY_WINDOW_SEC))

    def reset(self) -> None:
        """Reset scoring engine for a fresh round."""
        self.score = 0
        self.total_hits = 0
        self.total_throws = 0
        self.combo_tier_idx = 0
        self.max_combo = 1.0
        self.combo_timer = 0.0
        self.floating_scores.clear()

    def register_throw(self) -> None:
        """Track throws for accuracy metric."""
        self.total_throws += 1

    def register_hit(
        self,
        base_points: int,
        impact_speed: float,
        hit_pos: Tuple[float, float],
        color: Tuple[int, int, int]
    ) -> int:
        """
        Record a target hit, advance combo multiplier, and award calculated points.
        Points = (BasePoints * ComboMultiplier) + VelocityBonus.
        """
        self.total_hits += 1

        # Advance combo tier
        if self.combo_tier_idx < len(COMBO_TIERS) - 1:
            self.combo_tier_idx += 1
        current_mult = self.combo_multiplier
        if current_mult > self.max_combo:
            self.max_combo = current_mult

        # Reset decay timer
        self.combo_timer = COMBO_DECAY_WINDOW_SEC

        # Calculate bonuses
        velocity_bonus = int(impact_speed * 0.1)
        awarded_points = int(base_points * current_mult) + velocity_bonus
        self.score += awarded_points

        # Add floating popup
        self.floating_scores.append(FloatingScore(hit_pos[0], hit_pos[1], awarded_points, color))

        return awarded_points

    def update(self, dt: float) -> None:
        """Update combo decay timer and floating score popups."""
        if self.combo_tier_idx > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0.0:
                # Decay one tier
                self.combo_tier_idx -= 1
                if self.combo_tier_idx > 0:
                    self.combo_timer = COMBO_DECAY_WINDOW_SEC
                else:
                    self.combo_timer = 0.0

        # Update floating score animations
        self.floating_scores = [fs for fs in self.floating_scores if fs.update(dt)]
