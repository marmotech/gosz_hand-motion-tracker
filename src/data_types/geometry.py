"""Shared 2D positions and vectors for detection, calculation and display."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Point2D:
    """Input-image position in floating-point px; x right, y down from top left."""

    x: float
    y: float


@dataclass(frozen=True)
class Vector2D:
    """x/y components of velocity (px/s) or acceleration (px/s²)."""

    x: float
    y: float
