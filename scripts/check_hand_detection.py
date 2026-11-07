"""Detect hands in an image and print both hands' 21 positions as JSON."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_types.camera import CapturedFrame
from hand_detector import HandDetector


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Image to check (unmirrored)")
    args = parser.parse_args()

    try:
        image = cv2.imread(str(args.image))
        if image is None:
            raise ValueError(f"Cannot read image: {args.image}")
        # Stand in for camera-read completion time when checking a still image.
        frame = CapturedFrame(image=image, timestamp_ns=time.monotonic_ns())
        with HandDetector() as detector:
            result = detector.detect(frame)
        print(json.dumps(asdict(result), indent=2))
    except (OSError, ValueError, RuntimeError, cv2.error) as error:
        print(f"Hand detection check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
