"""Detect up to two hands in a captured frame with MediaPipe."""

from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision
from mediapipe.tasks.python.components.containers.landmark import NormalizedLandmark

from camera import CapturedFrame
from detection_types import DetectionResult, HandLandmarks
from geometry_types import Point2D


MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "hand_landmarker.task"


def _to_pixel_landmarks(
    landmarks: list[NormalizedLandmark], width: int, height: int
) -> HandLandmarks:
    """Convert one hand's normalized coordinates to floating-point image px."""
    points = []
    for point in landmarks:
        x_px = point.x * width
        y_px = point.y * height
        points.append(Point2D(x=x_px, y=y_px))

    return HandLandmarks(landmarks=tuple(points))


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

    def detect(self, frame: CapturedFrame) -> DetectionResult:
        """Return current positions in float px and the original capture time.

        Undetected hands are None. Previous positions are never substituted for
        the current observation. Inference/runtime errors propagate to callers.
        """
        if self._landmarker is None:
            raise RuntimeError("Hand detector is not open; use 'with HandDetector(...)'")

        rgb = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(image)
        height, width = frame.image.shape[:2]

        hands: dict[str, HandLandmarks] = {}
        scores: dict[str, float] = {}
        for landmarks, categories in zip(
            result.hand_landmarks, result.handedness, strict=True
        ):
            if not categories:
                continue
            category = max(categories, key=lambda item: item.score)
            side = category.category_name
            if side not in ("Left", "Right"):
                continue
            # A duplicate handedness label does not establish the other hand's
            # identity. Keep the more confident candidate for the same side.
            if side in scores and category.score <= scores[side]:
                continue
            hands[side] = _to_pixel_landmarks(landmarks, width, height)
            scores[side] = category.score

        return DetectionResult(
            timestamp_ns=frame.timestamp_ns,
            left=hands.get("Left"),
            right=hands.get("Right"),
        )

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        if self._landmarker is not None:
            landmarker = self._landmarker
            self._landmarker = None
            landmarker.close()
