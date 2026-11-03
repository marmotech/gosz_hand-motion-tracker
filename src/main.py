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
    try:
        with CameraCapture(args.camera) as camera:
            print("Camera started. Press Q or Esc in the window to quit.", flush=True)
            for frame in camera.frames():
                cv2.imshow(window_name, frame.image)
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
