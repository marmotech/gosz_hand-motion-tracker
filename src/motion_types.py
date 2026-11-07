"""Motion results shared by calculation and display, without camera dependencies."""

from dataclasses import dataclass

from detection_types import Point2D


@dataclass(frozen=True)
class Vector2D:
    """x/y components of velocity (px/s) or acceleration (px/s²)."""

    x: float
    y: float


@dataclass(frozen=True)
class LandmarkMotion:
    """One current position and its derivatives; unavailable vectors are None."""

    position: Point2D
    velocity: Vector2D | None = None
    acceleration: Vector2D | None = None


@dataclass(frozen=True)
class HandMotion:
    """All 21 points in HandLandmark order, including wrist and finger joints."""

    landmarks: tuple[LandmarkMotion, ...]

    def __post_init__(self) -> None:
        if len(self.landmarks) != 21:
            raise ValueError("A hand motion result must contain exactly 21 landmarks")


@dataclass(frozen=True)
class MotionResult:
    """Current measurements at the original capture time; missing hands are None."""

    timestamp_ns: int
    left: HandMotion | None = None
    right: HandMotion | None = None
