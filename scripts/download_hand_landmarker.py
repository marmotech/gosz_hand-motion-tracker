"""Download the pinned Hand Landmarker model from Google's official storage."""

import argparse
import hashlib
from pathlib import Path
import sys
from urllib.request import urlopen


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_SHA256 = "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "hand_landmarker.task"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Download again even if verified.")
    args = parser.parse_args()

    try:
        if MODEL_PATH.is_file() and not args.force:
            if hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest() == MODEL_SHA256:
                print(f"Model already verified: {MODEL_PATH}")
                return 0

        print(f"Downloading Hand Landmarker (float16, version 1): {MODEL_URL}", flush=True)
        with urlopen(MODEL_URL, timeout=30) as response:
            model_bytes = response.read()

        actual_sha256 = hashlib.sha256(model_bytes).hexdigest()
        if actual_sha256 != MODEL_SHA256:
            raise ValueError(f"Model checksum mismatch: {actual_sha256}")

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        MODEL_PATH.write_bytes(model_bytes)
    except (OSError, ValueError) as error:
        print(f"Model download failed: {error}", file=sys.stderr)
        return 1

    print(f"Saved verified model: {MODEL_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
