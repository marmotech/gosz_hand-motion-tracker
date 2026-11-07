"""Check the shared motion-result contract independently of calculation."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from detection_types import HandLandmark, Point2D
from motion_types import HandMotion, LandmarkMotion, MotionResult, Vector2D


class MotionTypesTests(unittest.TestCase):
    def test_named_landmarks_and_unavailable_vectors(self):
        points = [LandmarkMotion(Point2D(float(i), -float(i))) for i in range(21)]
        points[HandLandmark.WRIST] = LandmarkMotion(
            Point2D(0.0, 0.0), velocity=Vector2D(0.0, 0.0)
        )
        result = MotionResult(123, left=HandMotion(tuple(points)))
        self.assertIsNone(result.right)
        wrist = result.left.landmarks[HandLandmark.WRIST]
        self.assertEqual(wrist.velocity, Vector2D(0.0, 0.0))
        self.assertIsNone(wrist.acceleration)
        joint = result.left.landmarks[HandLandmark.INDEX_FINGER_PIP]
        self.assertEqual(joint.position, Point2D(6.0, -6.0))
        self.assertIsNone(joint.velocity)

    def test_rejects_incomplete_or_extra_landmarks(self):
        for count in (0, 20, 22):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    HandMotion(tuple(LandmarkMotion(Point2D(0, 0)) for _ in range(count)))


if __name__ == "__main__":
    unittest.main()
