"""Shared detection results, independent of MediaPipe and camera access."""

from dataclasses import dataclass
from enum import IntEnum

from geometry_types import Point2D


class HandLandmark(IntEnum):
    """Names for all 21 indices in MediaPipe landmark order."""

    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20


@dataclass(frozen=True)
class HandLandmarks:
    """One detected hand's 21 positions in MediaPipe landmark order.

    Coordinates belong to the input image, before any display transformations.
    Left/right identity is represented by the containing DetectionResult field.
    """

    landmarks: tuple[Point2D, ...]

    def __post_init__(self) -> None:
        if len(self.landmarks) != 21:
            raise ValueError("A detected hand must contain exactly 21 landmarks")


@dataclass(frozen=True)
class DetectionResult:
    """Current detections with the original CapturedFrame.timestamp_ns.

    Left/right follow MediaPipe handedness. An undetected hand is None;
    previous positions are never substituted for the current observation.
    timestamp_ns is the camera-read completion time, not inference time.
    """

    timestamp_ns: int
    left: HandLandmarks | None = None
    right: HandLandmarks | None = None
