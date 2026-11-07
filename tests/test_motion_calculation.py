"""Check numerical differences without a camera or a stateful calculator."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from detection_types import HandLandmarks, Point2D
from motion_calculation import calculate_hand_motion


BASE_NS = 10**18


def hand(displacement: float = 0.0) -> HandLandmarks:
    return HandLandmarks(tuple(
        Point2D(i + (i + 1) * displacement, 2 * i - 2 * (i + 1) * displacement)
        for i in range(21)
    ))


class MotionCalculationTests(unittest.TestCase):
    def test_first_observation_has_positions_and_no_derivatives(self):
        positions = hand()
        result = calculate_hand_motion(positions, BASE_NS)
        self.assertEqual(len(result.landmarks), 21)
        for i, point in enumerate(result.landmarks):
            self.assertEqual(point.position, positions.landmarks[i])
            self.assertIsNone(point.velocity)
            self.assertIsNone(point.acceleration)

    def test_all_points_with_irregular_intervals_and_large_timestamps(self):
        first = calculate_hand_motion(hand(), BASE_NS)
        second = calculate_hand_motion(hand(1), BASE_NS + 20_000_000, first, BASE_NS)
        third = calculate_hand_motion(
            hand(6), BASE_NS + 70_000_000, second, BASE_NS + 20_000_000
        )
        for i in range(21):
            scale = i + 1
            self.assertEqual(third.landmarks[i].position, hand(6).landmarks[i])
            self.assertAlmostEqual(second.landmarks[i].velocity.x, 50 * scale)
            self.assertAlmostEqual(second.landmarks[i].velocity.y, -100 * scale)
            self.assertIsNone(second.landmarks[i].acceleration)
            self.assertAlmostEqual(third.landmarks[i].velocity.x, 100 * scale)
            self.assertAlmostEqual(third.landmarks[i].velocity.y, -200 * scale)
            self.assertAlmostEqual(third.landmarks[i].acceleration.x, 1000 * scale)
            self.assertAlmostEqual(third.landmarks[i].acceleration.y, -2000 * scale)

    def test_stationary_hand_has_zero_vectors_not_none(self):
        first = calculate_hand_motion(hand(), 0)
        second = calculate_hand_motion(hand(), 20_000_000, first, 0)
        third = calculate_hand_motion(hand(), 40_000_000, second, 20_000_000)
        for point in third.landmarks:
            self.assertEqual((point.velocity.x, point.velocity.y), (0, 0))
            self.assertEqual((point.acceleration.x, point.acceleration.y), (0, 0))

    def test_nanosecond_precision_and_no_expiry_policy(self):
        first = calculate_hand_motion(hand(), BASE_NS)
        # Subtract integer timestamps before converting to floating-point seconds.
        second = calculate_hand_motion(hand(1), BASE_NS + 1, first, BASE_NS)
        self.assertAlmostEqual(second.landmarks[0].velocity.x, 1e9, delta=1e-6)
        # Retention policy belongs to the caller, not the numerical function.
        later = calculate_hand_motion(hand(1), BASE_NS + 1_000_000_000, first, BASE_NS)
        self.assertEqual(later.landmarks[0].velocity.x, 1.0)

    def test_previous_result_is_reusable_and_unchanged(self):
        first = calculate_hand_motion(hand(), 0)
        fast = calculate_hand_motion(hand(1), 20_000_000, first, 0)
        slow = calculate_hand_motion(hand(1), 40_000_000, first, 0)
        self.assertAlmostEqual(fast.landmarks[0].velocity.x, 50)
        self.assertAlmostEqual(slow.landmarks[0].velocity.x, 25)
        self.assertIsNone(first.landmarks[0].velocity)

    def test_previous_motion_requires_its_timestamp(self):
        first = calculate_hand_motion(hand(), 0)
        with self.assertRaises(ValueError):
            calculate_hand_motion(hand(), 1, previous=first)
        with self.assertRaises(ValueError):
            calculate_hand_motion(hand(), 1, previous_timestamp_ns=0)

    def test_rejects_nonincreasing_and_noninteger_timestamps(self):
        first = calculate_hand_motion(hand(), 20)
        for current in (19, 20, 20.5, True):
            with self.subTest(current=current):
                with self.assertRaises(ValueError):
                    calculate_hand_motion(hand(), current, first, 20)
        with self.assertRaises(ValueError):
            calculate_hand_motion(hand(), 30, first, 20.0)


if __name__ == "__main__":
    unittest.main()
