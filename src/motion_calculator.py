"""Calculate both hands' landmark motion using actual observation intervals."""

from dataclasses import dataclass
import math

from detection_types import DetectionResult, HandLandmarks
from motion_calculation import calculate_hand_motion, validate_timestamp_ns
from motion_types import HandMotion, MotionResult


@dataclass(frozen=True)
class _HandHistory:
    timestamp_ns: int
    motion: HandMotion


class MotionCalculator:
    """Keep independent left/right histories for at most retention_ms (default 100).

    Pass every DetectionResult, including frames with no hands. Timestamps must
    strictly increase. This class selects and retains previous observations;
    calculate_hand_motion handles the numerical differences without state.
    No missing observations are interpolated.
    """

    def __init__(self, retention_ms: float = 100.0) -> None:
        if not math.isfinite(retention_ms) or retention_ms < 0:
            raise ValueError("retention_ms must be finite and non-negative")
        self._retention_ns = round(retention_ms * 1_000_000)
        self._last_timestamp_ns: int | None = None
        self._left: _HandHistory | None = None
        self._right: _HandHistory | None = None

    def calculate(self, detection: DetectionResult) -> MotionResult:
        """Return current measurements without replacing missing hands by history.

        Reject duplicate/out-of-order timestamps before changing either history.
        Expiry is measured from the last detection, even if no intervening
        missing frame was passed. Exactly retention_ms is still retained.
        """
        timestamp_ns = detection.timestamp_ns
        validate_timestamp_ns(timestamp_ns)
        if self._last_timestamp_ns is not None and timestamp_ns <= self._last_timestamp_ns:
            raise ValueError("Capture timestamps must strictly increase")

        left, left_history = self._calculate_hand(detection.left, timestamp_ns, self._left)
        right, right_history = self._calculate_hand(detection.right, timestamp_ns, self._right)
        self._left = left_history
        self._right = right_history
        self._last_timestamp_ns = timestamp_ns
        return MotionResult(timestamp_ns=timestamp_ns, left=left, right=right)

    def _calculate_hand(
        self,
        hand: HandLandmarks | None,
        timestamp_ns: int,
        history: _HandHistory | None,
    ) -> tuple[HandMotion | None, _HandHistory | None]:
        if history is not None and timestamp_ns - history.timestamp_ns > self._retention_ns:
            history = None
        if hand is None:
            return None, history

        motion = calculate_hand_motion(
            hand,
            timestamp_ns,
            previous=history.motion if history is not None else None,
            previous_timestamp_ns=history.timestamp_ns if history is not None else None,
        )
        return motion, _HandHistory(timestamp_ns=timestamp_ns, motion=motion)
