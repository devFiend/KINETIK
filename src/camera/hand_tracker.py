"""MediaPipe HandLandmarker wrapper for 21-landmark tracking with normalized coordinates."""
from dataclasses import dataclass, field
import os
import urllib.request
from typing import List, Optional, Tuple
import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision
import numpy as np

# Official Google MediaPipe HandLandmarker task model URL
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "assets",
    "models",
    "hand_landmarker.task"
)

# Standard Hand Skeleton Connection Topology (pairs of landmark indices)
HAND_CONNECTIONS = [
    # Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Index finger
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Middle finger
    (9, 10), (10, 11), (11, 12),
    # Ring finger
    (13, 14), (14, 15), (15, 16),
    # Pinky
    (0, 17), (17, 18), (18, 19), (19, 20),
    # Palm knuckles
    (5, 9), (9, 13), (13, 17)
]


@dataclass
class LandmarkPoint:
    """A single 3D normalized landmark point."""
    x: float  # Normalized [0.0, 1.0]
    y: float  # Normalized [0.0, 1.0]
    z: float  # Depth relative to wrist


@dataclass
class HandData:
    """Normalized landmarks and metadata for one tracked hand."""
    handedness: str  # "Left" or "Right"
    confidence: float
    landmarks: List[LandmarkPoint] = field(default_factory=list)

    @property
    def wrist(self) -> LandmarkPoint:
        return self.landmarks[0]

    @property
    def thumb_tip(self) -> LandmarkPoint:
        return self.landmarks[4]

    @property
    def index_tip(self) -> LandmarkPoint:
        return self.landmarks[8]

    @property
    def hand_center(self) -> LandmarkPoint:
        """Midpoint between wrist (0) and middle MCP (9) representing palm center."""
        w, m = self.landmarks[0], self.landmarks[9]
        return LandmarkPoint(
            x=(w.x + m.x) * 0.5,
            y=(w.y + m.y) * 0.5,
            z=(w.z + m.z) * 0.5
        )


class HandTracker:
    """
    Wraps MediaPipe HandLandmarker to process BGR video frames into structured hand landmarks.
    """

    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        num_hands: int = 2,
        min_hand_detection_confidence: float = 0.5,
        min_hand_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        self.model_path = model_path
        self.num_hands = num_hands
        self.min_detection_confidence = min_hand_detection_confidence
        self.min_presence_confidence = min_hand_presence_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self._ensure_model_exists()
        self._landmarker: Optional[vision.HandLandmarker] = None
        self._initialize_landmarker()

    def _ensure_model_exists(self) -> None:
        """Verify model file exists on disk, downloading if missing."""
        if not os.path.exists(self.model_path):
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            print(f"[HandTracker] Downloading MediaPipe model to {self.model_path}...")
            urllib.request.urlretrieve(MODEL_URL, self.model_path)
            print("[HandTracker] Model download complete.")

    def _initialize_landmarker(self) -> None:
        """Instantiate HandLandmarker from task model."""
        base_options = BaseOptions(model_asset_path=self.model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=self.num_hands,
            min_hand_detection_confidence=self.min_detection_confidence,
            min_hand_presence_confidence=self.min_presence_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

    def process_frame(self, bgr_frame: np.ndarray) -> List[HandData]:
        """
        Process an OpenCV BGR frame and return detected hands with normalized landmarks.
        """
        if self._landmarker is None or bgr_frame is None or bgr_frame.size == 0:
            return []

        # Convert OpenCV BGR to RGB
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self._landmarker.detect(mp_image)
        if not result.hand_landmarks:
            return []

        detected_hands: List[HandData] = []

        for hand_idx, landmarks in enumerate(result.hand_landmarks):
            # Extract handedness label and score if available
            handedness_label = "Right"
            confidence = 0.9
            if result.handedness and hand_idx < len(result.handedness):
                categories = result.handedness[hand_idx]
                if categories:
                    handedness_label = categories[0].category_name
                    confidence = categories[0].score

            points = [
                LandmarkPoint(x=lm.x, y=lm.y, z=lm.z)
                for lm in landmarks
            ]

            detected_hands.append(HandData(
                handedness=handedness_label,
                confidence=confidence,
                landmarks=points
            ))

        return detected_hands

    def close(self) -> None:
        """Release underlying model resources."""
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None
