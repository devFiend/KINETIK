"""Pinch distance calculation with dual-threshold Schmitt trigger hysteresis."""
import math
from typing import Tuple
from src.camera.hand_tracker import LandmarkPoint
from src.config import PINCH_DEBOUNCE_FRAMES, PINCH_ENTER_THRESHOLD, PINCH_EXIT_THRESHOLD


class PinchDetector:
    """
    Calculates 3D Euclidean distance between thumb and index tips.
    Implements a Schmitt trigger with hysteresis and multi-frame debounce to prevent flickering.
    """

    def __init__(
        self,
        enter_threshold: float = PINCH_ENTER_THRESHOLD,
        exit_threshold: float = PINCH_EXIT_THRESHOLD,
        debounce_frames: int = PINCH_DEBOUNCE_FRAMES
    ):
        assert enter_threshold < exit_threshold, "enter_threshold must be strictly less than exit_threshold"
        self.enter_threshold = enter_threshold
        self.exit_threshold = exit_threshold
        self.debounce_frames = debounce_frames

        self._is_pinched = False
        self._candidate_state = False
        self._candidate_count = 0
        self._current_distance = 1.0

    @property
    def is_pinched(self) -> bool:
        """Current confirmed pinch state."""
        return self._is_pinched

    @property
    def distance(self) -> float:
        """Last measured 3D Euclidean pinch distance."""
        return self._current_distance

    def reset(self) -> None:
        """Reset hysteresis state machine."""
        self._is_pinched = False
        self._candidate_state = False
        self._candidate_count = 0
        self._current_distance = 1.0

    def compute_distance(self, thumb_tip: LandmarkPoint, index_tip: LandmarkPoint) -> float:
        """Compute Euclidean distance in 3D landmark space."""
        dx = index_tip.x - thumb_tip.x
        dy = index_tip.y - thumb_tip.y
        dz = index_tip.z - thumb_tip.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def get_pinch_factor(self, max_open_dist: float = 0.20) -> float:
        """
        Normalized pinch factor in range [0.0, 1.0] for animation.
        - 0.0 = completely open fingers.
        - 1.0 = fingers tightly pinched.
        """
        clamped = max(self.enter_threshold, min(max_open_dist, self._current_distance))
        # Linear interpolation inverted
        factor = 1.0 - (clamped - self.enter_threshold) / (max_open_dist - self.enter_threshold)
        return max(0.0, min(1.0, factor))

    def update(self, thumb_tip: LandmarkPoint, index_tip: LandmarkPoint) -> Tuple[bool, bool, bool]:
        """
        Update detector with fresh tip landmarks.
        Returns:
            (is_pinched, just_pinched, just_released)
        """
        self._current_distance = self.compute_distance(thumb_tip, index_tip)

        target_state = self._is_pinched
        if not self._is_pinched and self._current_distance <= self.enter_threshold:
            target_state = True
        elif self._is_pinched and self._current_distance >= self.exit_threshold:
            target_state = False

        just_pinched = False
        just_released = False

        if target_state != self._is_pinched:
            if target_state == self._candidate_state:
                self._candidate_count += 1
            else:
                self._candidate_state = target_state
                self._candidate_count = 1

            # Require debounce persistence before switching confirmed state
            if self._candidate_count >= self.debounce_frames:
                self._is_pinched = target_state
                self._candidate_count = 0
                if self._is_pinched:
                    just_pinched = True
                else:
                    just_released = True
        else:
            self._candidate_count = 0

        return self._is_pinched, just_pinched, just_released
