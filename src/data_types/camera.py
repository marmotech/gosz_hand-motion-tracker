"""Camera frame data shared by capture and detection."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CapturedFrame:
    """A BGR camera frame and its capture-read completion time."""

    image: np.ndarray
    timestamp_ns: int
