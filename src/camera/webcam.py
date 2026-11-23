"""Threaded webcam frame capture with OpenCV and decoupled buffering."""
import platform
import threading
import time
from typing import Optional, Tuple
import cv2
import numpy as np

from src.config import DEFAULT_CAM_WIDTH, DEFAULT_CAM_HEIGHT, DEFAULT_CAMERA_INDEX, DEFAULT_MIRROR_MODE


class WebcamCapture:
    """
    Manages asynchronous webcam capture on a dedicated background thread.
    Prevents OpenCV driver I/O latency from dropping Pygame/Pymunk rendering frames.
    """

    def __init__(
        self,
        camera_index: int = DEFAULT_CAMERA_INDEX,
        width: int = DEFAULT_CAM_WIDTH,
        height: int = DEFAULT_CAM_HEIGHT,
        mirror: bool = DEFAULT_MIRROR_MODE,
        mock_mode: bool = False,
    ):
        self.camera_index = camera_index
        self.target_width = width
        self.target_height = height
        self.mirror = mirror
        self.mock_mode = mock_mode

        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._latest_frame: Optional[np.ndarray] = None
        self._frame_timestamp: float = 0.0
        self._frame_count: int = 0
        self._fps: float = 0.0
        self._is_available: bool = False
        self._error_message: Optional[str] = None

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def error_message(self) -> Optional[str]:
        return self._error_message

    @property
    def fps(self) -> float:
        return self._fps

    def start(self) -> bool:
        """Start the background capture worker."""
        if self._running:
            return True

        if self.mock_mode:
            self._is_available = True
            self._running = True
            self._thread = threading.Thread(target=self._mock_worker, daemon=True)
            self._thread.start()
            return True

        # On Windows, DirectShow (CAP_DSHOW) initializes much faster than MSMF
        api_preference = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY

        try:
            self._cap = cv2.VideoCapture(self.camera_index, api_preference)
            if not self._cap or not self._cap.isOpened():
                # Fallback to default API if DSHOW failed
                self._cap = cv2.VideoCapture(self.camera_index)

            if not self._cap.isOpened():
                self._is_available = False
                self._error_message = f"Could not open camera at index {self.camera_index}"
                return False

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)

            self._is_available = True
            self._error_message = None
            self._running = True
            self._thread = threading.Thread(target=self._capture_worker, daemon=True)
            self._thread.start()
            return True

        except Exception as e:
            self._is_available = False
            self._error_message = str(e)
            return False

    def _capture_worker(self) -> None:
        """Background thread continuously polling camera frames."""
        fps_counter = 0
        fps_timer = time.time()

        while self._running:
            if not self._cap or not self._cap.isOpened():
                time.sleep(0.05)
                continue

            ret, frame = self._cap.read()
            if not ret or frame is None:
                with self._lock:
                    self._is_available = False
                    self._error_message = "Camera read failed or disconnected"
                time.sleep(0.05)
                continue

            # Apply horizontal flip if mirrored
            if self.mirror:
                frame = cv2.flip(frame, 1)

            current_time = time.time()
            fps_counter += 1
            if current_time - fps_timer >= 1.0:
                self._fps = fps_counter / (current_time - fps_timer)
                fps_counter = 0
                fps_timer = current_time

            with self._lock:
                self._latest_frame = frame
                self._frame_timestamp = current_time
                self._frame_count += 1
                self._is_available = True
                self._error_message = None

            # Yield briefly to maintain healthy CPU scheduling
            time.sleep(0.005)

    def _mock_worker(self) -> None:
        """Generates synthetic video frames for headless testing and CI."""
        fps_counter = 0
        fps_timer = time.time()

        while self._running:
            # Generate a test pattern frame (dark gradient with timestamp)
            frame = np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
            frame[:, :] = (20, 25, 35)

            current_time = time.time()
            fps_counter += 1
            if current_time - fps_timer >= 1.0:
                self._fps = fps_counter / (current_time - fps_timer)
                fps_counter = 0
                fps_timer = current_time

            with self._lock:
                self._latest_frame = frame
                self._frame_timestamp = current_time
                self._frame_count += 1

            time.sleep(0.033)  # ~30 FPS

    def get_latest_frame(self) -> Tuple[Optional[np.ndarray], float]:
        """Thread-safe retrieval of the freshest camera frame and timestamp."""
        with self._lock:
            if self._latest_frame is None:
                return None, 0.0
            return self._latest_frame.copy(), self._frame_timestamp

    def toggle_mirror(self) -> bool:
        """Toggle horizontal mirror flip."""
        self.mirror = not self.mirror
        return self.mirror

    def stop(self) -> None:
        """Cleanly stop worker thread and release hardware handle."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None

        if self._cap:
            self._cap.release()
            self._cap = None

        self._is_available = False
