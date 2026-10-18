"""Check that Hand Landmarker can initialize and close with the local model."""

from pathlib import Path
import sys

from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python import vision


MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "hand_landmarker.task"


def main() -> int:
    if not MODEL_PATH.is_file():
        print(f"Model not found: {MODEL_PATH}", file=sys.stderr)
        print(
            "Download it first: uv run --locked python scripts/download_hand_landmarker.py",
            file=sys.stderr,
        )
        return 1

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=str(MODEL_PATH), delegate=BaseOptions.Delegate.CPU
        ),
        running_mode=vision.RunningMode.IMAGE,
    )
    try:
        with vision.HandLandmarker.create_from_options(options):
            print("Hand Landmarker initialized.", flush=True)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Hand Landmarker check failed: {error}", file=sys.stderr)
        return 1

    print("Hand Landmarker closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
