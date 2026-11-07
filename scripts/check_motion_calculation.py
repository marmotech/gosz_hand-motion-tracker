"""Print sample positions and the motion calculated by the application module."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_types.detection import DetectionResult, HandLandmark, HandLandmarks
from data_types.geometry import Point2D, Vector2D
from motion_calculator import MotionCalculator


def make_hand(offset: float | None) -> HandLandmarks | None:
    """Give each landmark a different displacement; None means no detection."""
    if offset is None:
        return None
    return HandLandmarks(tuple(
        Point2D(10 * i + (i + 1) * offset, 5 * i - 2 * (i + 1) * offset)
        for i in range(21)
    ))


def format_vector(value: Point2D | Vector2D | None) -> str:
    if value is None:
        return "None"
    return f"({value.x:.3f}, {value.y:.3f})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--landmark", choices=list(HandLandmark.__members__), default="WRIST")
    parser.add_argument("--retention-ms", type=float, default=100.0)
    args = parser.parse_args()
    try:
        calculator = MotionCalculator(retention_ms=args.retention_ms)
    except ValueError as error:
        parser.error(str(error))
    landmark = HandLandmark[args.landmark]

    # Synthetic capture times (ms), left offset, right offset.
    # Left briefly disappears, recovers, then disappears for more than 100ms.
    # Right stays detected so its independent history can be observed.
    observations = [
        (0, 0.0, 0.0),
        (20, 1.0, -1.0),
        (70, 6.0, -6.0),
        (90, None, -8.0),
        (120, 11.0, -11.0),
        (180, None, -17.0),
        (220, None, -21.0),
        (240, 23.0, -23.0),
        (260, 25.0, -25.0),
        (280, 27.0, -27.0),
    ]
    print(f"Landmark: {landmark.name}; retention: {args.retention_ms:g} ms")
    print("Synthetic input; all 21 landmarks are calculated. Vectors are (x, y).")
    print(f"{'t(ms)':>6} {'hand':5} {'input position(px)':>24} "
          f"{'velocity(px/s)':>24} {'acceleration(px/s^2)':>24}")
    for ms, left_offset, right_offset in observations:
        detection = DetectionResult(
            timestamp_ns=ms * 1_000_000,
            left=make_hand(left_offset),
            right=make_hand(right_offset),
        )
        result = calculator.calculate(detection)
        for side in ("left", "right"):
            hand = getattr(detection, side)
            motion = getattr(result, side)
            position = hand.landmarks[landmark] if hand is not None else None
            point = motion.landmarks[landmark] if motion is not None else None
            velocity = point.velocity if point is not None else None
            acceleration = point.acceleration if point is not None else None
            print(f"{ms:6d} {side:5} {format_vector(position):>24} "
                  f"{format_vector(velocity):>24} {format_vector(acceleration):>24}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
