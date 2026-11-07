"""Check independent hand histories, missing observations and expiration."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from detection_types import DetectionResult, HandLandmarks, Point2D
from motion_calculator import MotionCalculator
from motion_types import HandMotion


BASE_NS = 10**18


def hand(displacement: float = 0.0) -> HandLandmarks:
    # Every point has a different velocity, including wrist and non-tip joints.
    return HandLandmarks(tuple(
        Point2D(i + (i + 1) * displacement, 2 * i - 2 * (i + 1) * displacement)
        for i in range(21)
    ))


def frame(ms: int, left=None, right=None) -> DetectionResult:
    return DetectionResult(BASE_NS + ms * 1_000_000, left, right)


class MotionCalculatorTests(unittest.TestCase):
    def assert_uncomputed(self, motion: HandMotion) -> None:
        self.assertEqual(len(motion.landmarks), 21)
        for point in motion.landmarks:
            self.assertIsNone(point.velocity)
            self.assertIsNone(point.acceleration)

    def test_short_gap_retains_velocity_and_uses_time_since_last_detection(self):
        calculator = MotionCalculator()
        calculator.calculate(frame(0, hand()))
        calculator.calculate(frame(20, hand(1)))
        missing = calculator.calculate(frame(40))
        self.assertEqual(missing.timestamp_ns, BASE_NS + 40_000_000)
        self.assertIsNone(missing.left)
        self.assertIsNone(missing.right)
        result = calculator.calculate(frame(70, hand(6)))
        for i, point in enumerate(result.left.landmarks):
            self.assertAlmostEqual(point.velocity.x, 100 * (i + 1))
            self.assertAlmostEqual(point.acceleration.x, 1000 * (i + 1))

    def test_missing_frames_do_not_refresh_expiry(self):
        calculator = MotionCalculator()
        calculator.calculate(frame(0, hand()))
        calculator.calculate(frame(20, hand(1)))
        calculator.calculate(frame(70))
        calculator.calculate(frame(121))
        result = calculator.calculate(frame(130, hand(10)))
        self.assert_uncomputed(result.left)
        next_result = calculator.calculate(frame(150, hand(11)))
        self.assertIsNotNone(next_result.left.landmarks[0].velocity)
        self.assertIsNone(next_result.left.landmarks[0].acceleration)

    def test_expiry_without_intermediate_missing_frames(self):
        calculator = MotionCalculator()
        calculator.calculate(frame(0, hand()))
        result = calculator.calculate(frame(101, hand(10)))
        self.assert_uncomputed(result.left)

    def test_retention_boundary_is_inclusive(self):
        for interval in (99, 100, 101):
            with self.subTest(interval=interval):
                calculator = MotionCalculator()
                calculator.calculate(frame(0, hand()))
                result = calculator.calculate(frame(interval, hand(1)))
                if interval <= 100:
                    self.assertAlmostEqual(result.left.landmarks[0].velocity.x, 1000 / interval)
                else:
                    self.assert_uncomputed(result.left)

    def test_custom_retention_and_zero_retention(self):
        calculator = MotionCalculator(retention_ms=200)
        calculator.calculate(frame(0, hand()))
        self.assertIsNotNone(calculator.calculate(frame(150, hand(1))).left.landmarks[0].velocity)
        calculator = MotionCalculator(retention_ms=0)
        calculator.calculate(frame(0, hand()))
        self.assert_uncomputed(calculator.calculate(frame(1, hand(1))).left)

    def test_left_and_right_histories_are_independent(self):
        calculator = MotionCalculator()
        calculator.calculate(frame(0, hand(), hand()))
        calculator.calculate(frame(50, right=hand(1)))
        result = calculator.calculate(frame(101, hand(10), hand(3)))
        self.assert_uncomputed(result.left)
        self.assertAlmostEqual(result.right.landmarks[0].velocity.x, 2 / .051)
        self.assertAlmostEqual(result.right.landmarks[0].acceleration.x, (2 / .051 - 20) / .051)

    def test_initial_missing_hand_starts_new_series(self):
        calculator = MotionCalculator()
        calculator.calculate(frame(0))
        result = calculator.calculate(frame(20, right=hand()))
        self.assertIsNone(result.left)
        self.assert_uncomputed(result.right)

    def test_gap_after_first_position_preserves_it_without_inventing_velocity(self):
        calculator = MotionCalculator()
        first = calculator.calculate(frame(0, hand()))
        calculator.calculate(frame(20))
        second = calculator.calculate(frame(40, hand(1)))
        self.assertAlmostEqual(second.left.landmarks[0].velocity.x, 25)
        self.assertIsNone(second.left.landmarks[0].acceleration)
        # Later calculations must not mutate an earlier result.
        self.assert_uncomputed(first.left)

    def test_invalid_timestamps_do_not_change_history(self):
        calculator = MotionCalculator()
        calculator.calculate(frame(20, hand(), hand()))
        for timestamp in (BASE_NS + 20_000_000, BASE_NS, 1.5, True):
            with self.subTest(timestamp=timestamp):
                with self.assertRaises(ValueError):
                    calculator.calculate(DetectionResult(timestamp, hand(100), hand(100)))
        result = calculator.calculate(frame(40, hand(1), hand(2)))
        self.assertAlmostEqual(result.left.landmarks[0].velocity.x, 50)
        self.assertAlmostEqual(result.right.landmarks[0].velocity.x, 100)

    def test_invalid_retention(self):
        for retention in (-1, float("nan"), float("inf")):
            with self.subTest(retention=retention):
                with self.assertRaises(ValueError):
                    MotionCalculator(retention_ms=retention)


if __name__ == "__main__":
    unittest.main()
