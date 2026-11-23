"""Gesture state machine aggregating pinch, velocity, and pose classification."""
from enum import Enum, auto
import time
from typing import Dict, List, Optional, Tuple
from src.camera.hand_tracker import HandData
from src.gestures.motion import AdaptiveEMASmoother2D, RollingVelocityEstimator
from src.gestures.pinch import PinchDetector


class GestureType(Enum):
    """Classified high-level user gesture."""
    NONE = auto()
    HOVER = auto()
    PINCH = auto()
    RELEASE = auto()
    PUSH = auto()


class HandGestureState:
    """Consolidated gesture telemetry and filtered coordinates for a single tracked hand."""

    def __init__(self, handedness: str):
        self.handedness = handedness
        self.pinch_detector = PinchDetector()
        self.smoother = AdaptiveEMASmoother2D()
        self.velocity_estimator = RollingVelocityEstimator()

        self.screen_pos: Tuple[float, float] = (0.0, 0.0)
        self.raw_screen_pos: Tuple[float, float] = (0.0, 0.0)
        self.velocity: Tuple[float, float] = (0.0, 0.0)
        self.speed: float = 0.0
        self.pinch_distance: float = 1.0
        self.pinch_factor: float = 0.0
        self.is_pinched: bool = False
        self.just_pinched: bool = False
        self.just_released: bool = False
        self.gesture_type: GestureType = GestureType.HOVER
        self.last_seen_time: float = 0.0

    def update(
        self,
        hand: HandData,
        screen_width: int,
        screen_height: int,
        now: Optional[float] = None
    ) -> None:
        """Process updated hand landmarks into filtered screen state and gestures."""
        t = now if now is not None else time.time()
        self.last_seen_time = t

        # Anchor point is the midpoint between thumb tip and index tip (interaction focal point)
        thumb = hand.thumb_tip
        index = hand.index_tip
        anchor_x_norm = (thumb.x + index.x) * 0.5
        anchor_y_norm = (thumb.y + index.y) * 0.5

        # Map to screen pixels
        raw_x = anchor_x_norm * screen_width
        raw_y = anchor_y_norm * screen_height
        self.raw_screen_pos = (raw_x, raw_y)

        # Smooth coordinates
        self.screen_pos = self.smoother.filter(raw_x, raw_y, timestamp=t)

        # Update velocity
        self.velocity_estimator.add_sample(self.screen_pos[0], self.screen_pos[1], timestamp=t)
        vx, vy, speed = self.velocity_estimator.get_velocity()
        self.velocity = (vx, vy)
        self.speed = speed

        # Update pinch hysteresis
        is_p, just_p, just_r = self.pinch_detector.update(thumb, index)
        self.is_pinched = is_p
        self.just_pinched = just_p
        self.just_released = just_r
        self.pinch_distance = self.pinch_detector.distance
        self.pinch_factor = self.pinch_detector.get_pinch_factor()

        # Classify gesture state
        if just_r:
            self.gesture_type = GestureType.RELEASE
        elif is_p:
            self.gesture_type = GestureType.PINCH
        elif speed > 1200.0:
            self.gesture_type = GestureType.PUSH
        else:
            self.gesture_type = GestureType.HOVER


class GestureDetector:
    """
    Coordinates gesture recognition across all active hands.
    Maintains persistent tracking states indexed by handedness ("Left", "Right").
    """

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._states: Dict[str, HandGestureState] = {
            "Right": HandGestureState("Right"),
            "Left": HandGestureState("Left"),
        }

    def process_hands(self, hands: List[HandData], now: Optional[float] = None) -> List[HandGestureState]:
        """
        Update gesture states for all visible hands and return active states.
        """
        current_time = now if now is not None else time.time()
        active_states: List[HandGestureState] = []

        seen_hands = set()
        for hand in hands:
            handedness = hand.handedness
            if handedness not in self._states:
                self._states[handedness] = HandGestureState(handedness)

            state = self._states[handedness]
            state.update(hand, self.screen_width, self.screen_height, now=current_time)
            active_states.append(state)
            seen_hands.add(handedness)

        return active_states

    def get_primary_hand(self, active_states: List[HandGestureState]) -> Optional[HandGestureState]:
        """Return the primary active hand (prioritizing Right hand or currently pinched hand)."""
        if not active_states:
            return None
        for state in active_states:
            if state.is_pinched:
                return state
        for state in active_states:
            if state.handedness == "Right":
                return state
        return active_states[0]
