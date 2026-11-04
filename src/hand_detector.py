"""Detect up to two hands in a captured frame with MediaPipe."""

from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

from camera import CapturedFrame


MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "hand_landmarker.task"


class HandDetector:
    """Manage a CPU Hand Landmarker and detect up to two hands per image.

    IMAGE mode processes each frame synchronously without timestamp conversion
    or tracking state. Pass unmirrored BGR camera images; left/right labels
    follow MediaPipe handedness without an application-level identity tracker.
    """

    def __init__(self, model_path: str | Path = MODEL_PATH) -> None:
        self.model_path = Path(model_path)
        self._landmarker: vision.HandLandmarker | None = None

    def __enter__(self) -> "HandDetector":
        if self._landmarker is not None:
            raise RuntimeError("Hand detector is already open")
        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"Model not found: {self.model_path}. Download it first: "
                "uv run --locked python scripts/download_hand_landmarker.py"
            )

        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(
                model_asset_path=str(self.model_path),
                delegate=BaseOptions.Delegate.CPU,
            ),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        return self

    def detect(self, frame: CapturedFrame) -> vision.HandLandmarkerResult:
        """Return MediaPipe's normalized landmarks and handedness for this image."""
        if self._landmarker is None:
            raise RuntimeError("Hand detector is not open; use 'with HandDetector(...)'")

        rgb = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        return self._landmarker.detect(image)

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        if self._landmarker is not None:
            landmarker = self._landmarker
            self._landmarker = None
            landmarker.close()
