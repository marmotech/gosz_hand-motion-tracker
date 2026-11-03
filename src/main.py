"""Run the hand motion tracker."""

import argparse
import sys

import cv2

from camera import CameraCapture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    args = parser.parse_args()

    window_name = "Hand Motion Tracker"
    previous_timestamp_ns = None
    try:
        with CameraCapture(args.camera) as camera:
            print("Camera started. Press Q or Esc in the window to quit.", flush=True)
            for frame in camera.frames():
                interval = "N/A"
                if previous_timestamp_ns is not None:
                    interval_ms = (frame.timestamp_ns - previous_timestamp_ns) / 1_000_000
                    interval = f"{interval_ms:.3f} ms"
                previous_timestamp_ns = frame.timestamp_ns

                image = frame.image.copy()
                lines = (
                    f"Capture timestamp: {frame.timestamp_ns} ns",
                    f"Frame interval: {interval}",
                )
                for index, line in enumerate(lines):
                    position = (10, 30 + index * 28)
                    cv2.putText(
                        image, line, position, cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 255), 1, cv2.LINE_AA,
                    )
                cv2.imshow(window_name, image)
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q"), 27):
                    break
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
    except KeyboardInterrupt:
        pass
    except (RuntimeError, cv2.error) as error:
        print(f"Hand Motion Tracker failed: {error}", file=sys.stderr)
        return 1
    finally:
        cv2.destroyAllWindows()

    print("Camera stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
