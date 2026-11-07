"""Calculate both hands' landmark motion using actual observation intervals."""

from dataclasses import dataclass
import math

from data_types.detection import DetectionResult, HandLandmarks
from data_types.geometry import Vector2D
from data_types.motion import HandMotion, LandmarkMotion, MotionResult


def _validate_timestamp_ns(timestamp_ns: int) -> None:
    """Require integer capture times before computing differences or saving state."""
    if not isinstance(timestamp_ns, int) or isinstance(timestamp_ns, bool):
        raise ValueError("timestamp_ns must be an integer number of nanoseconds")


def _calculate_hand_motion(
    hand: HandLandmarks,
    timestamp_ns: int,
    previous: HandMotion | None = None,
    previous_timestamp_ns: int | None = None,
    previous_interval_ns: int | None = None,
) -> HandMotion:
    """Calculate 21 points without keeping history or deciding its expiration.

    Supply both previous arguments or neither. With no previous observation,
    return positions with unavailable derivatives. Otherwise use actual capture
    time differences. Velocities are interval averages. Acceleration uses the
    time between the midpoints of the previous and current velocity intervals.
    """
    _validate_timestamp_ns(timestamp_ns)
    if (previous is None) != (previous_timestamp_ns is None):
        raise ValueError("Previous motion and its capture timestamp must be supplied together")
    if previous is None:
        return HandMotion(tuple(LandmarkMotion(position) for position in hand.landmarks))

    _validate_timestamp_ns(previous_timestamp_ns)
    if timestamp_ns <= previous_timestamp_ns:
        raise ValueError("Capture timestamps must strictly increase")
    interval_ns = timestamp_ns - previous_timestamp_ns
    dt = interval_ns / 1_000_000_000
    points = []
    for position, prior in zip(hand.landmarks, previous.landmarks, strict=True):
        velocity = Vector2D(
            x=(position.x - prior.position.x) / dt,
            y=(position.y - prior.position.y) / dt,
        )
        acceleration = None
        if prior.velocity is not None and previous_interval_ns is not None:
            acceleration_dt = (previous_interval_ns + interval_ns) / 2_000_000_000
            acceleration = Vector2D(
                x=(velocity.x - prior.velocity.x) / acceleration_dt,
                y=(velocity.y - prior.velocity.y) / acceleration_dt,
            )
        points.append(LandmarkMotion(position, velocity, acceleration))
    return HandMotion(tuple(points))


@dataclass(frozen=True)
class _HandHistory:
    timestamp_ns: int
    motion: HandMotion
    interval_ns: int | None


class MotionCalculator:
    """Keep independent left/right histories for at most retention_ms (default 100).

    Pass every DetectionResult, including frames with no hands. Timestamps must
    strictly increase. This class selects and retains previous observations;
    _calculate_hand_motion handles the numerical differences without state.
    A hand containing non-finite x/y coordinates is treated as missing.
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
        _validate_timestamp_ns(timestamp_ns)
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
        if any(
            not math.isfinite(point.x) or not math.isfinite(point.y)
            for point in hand.landmarks
        ):
            return None, history

        motion = _calculate_hand_motion(
            hand,
            timestamp_ns,
            previous=history.motion if history is not None else None,
            previous_timestamp_ns=history.timestamp_ns if history is not None else None,
            previous_interval_ns=history.interval_ns if history is not None else None,
        )
        interval_ns = timestamp_ns - history.timestamp_ns if history is not None else None
        return motion, _HandHistory(
            timestamp_ns=timestamp_ns, motion=motion, interval_ns=interval_ns
        )
