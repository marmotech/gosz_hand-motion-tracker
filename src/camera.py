"""Capture webcam frames with monotonic timestamps.

Example:
    with CameraCapture(0) as camera:
        for sample in camera.frames():
            print(sample.timestamp_ns, sample.image.shape)
            if should_stop():
                break
"""

from dataclasses import dataclass
import time
from typing import Iterator

import cv2
import numpy as np


@dataclass(frozen=True)
class CapturedFrame:
    """A BGR camera frame and its capture-read completion time."""

    image: np.ndarray
    timestamp_ns: int


class CameraCapture:
    """Manage a camera and yield successfully read frames."""

    def __init__(self, device_index: int = 0) -> None:
        self.device_index = device_index
        self._capture: cv2.VideoCapture | None = None

    def __enter__(self) -> "CameraCapture":
        if self._capture is not None:
            raise RuntimeError("Camera is already open")

        capture = cv2.VideoCapture(self.device_index)
        if not capture.isOpened():
            capture.release()
            raise RuntimeError(f"Cannot open camera {self.device_index}")

        self._capture = capture
        return self

    def frames(self) -> Iterator[CapturedFrame]:
        """Yield frames until read fails or the caller stops iteration.

        A failed read raises RuntimeError; normal early exit is handled by
        leaving the enclosing context manager.
        """
        capture = self._capture
        if capture is None:
            raise RuntimeError("Camera is not open; use 'with CameraCapture(...)'")

        while True:
            success, image = capture.read()
            if not success or image is None:
                raise RuntimeError(f"Failed to read frame from camera {self.device_index}")
            timestamp_ns = time.monotonic_ns()
            yield CapturedFrame(image=image, timestamp_ns=timestamp_ns)

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
