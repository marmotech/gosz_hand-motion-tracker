"""Stateless differences of landmark positions and velocities."""

from detection_types import HandLandmarks
from motion_types import HandMotion, LandmarkMotion, Vector2D


def validate_timestamp_ns(timestamp_ns: int) -> None:
    """Require integer capture times before computing differences or saving state."""
    if not isinstance(timestamp_ns, int) or isinstance(timestamp_ns, bool):
        raise ValueError("timestamp_ns must be an integer number of nanoseconds")


def calculate_hand_motion(
    hand: HandLandmarks,
    timestamp_ns: int,
    previous: HandMotion | None = None,
    previous_timestamp_ns: int | None = None,
) -> HandMotion:
    """Calculate 21 points without keeping history or deciding its expiration.

    Supply both previous arguments or neither. With no previous observation,
    return positions with unavailable derivatives. Otherwise use actual capture
    time differences; previous velocities belong to previous_timestamp_ns.
    Current velocities belong to timestamp_ns, not the interval midpoint.
    """
    validate_timestamp_ns(timestamp_ns)
    if (previous is None) != (previous_timestamp_ns is None):
        raise ValueError("Previous motion and its capture timestamp must be supplied together")
    if previous is None:
        return HandMotion(tuple(LandmarkMotion(position) for position in hand.landmarks))

    validate_timestamp_ns(previous_timestamp_ns)
    if timestamp_ns <= previous_timestamp_ns:
        raise ValueError("Capture timestamps must strictly increase")
    dt = (timestamp_ns - previous_timestamp_ns) / 1_000_000_000
    points = []
    for position, prior in zip(hand.landmarks, previous.landmarks, strict=True):
        velocity = Vector2D(
            x=(position.x - prior.position.x) / dt,
            y=(position.y - prior.position.y) / dt,
        )
        acceleration = None
        if prior.velocity is not None:
            acceleration = Vector2D(
                x=(velocity.x - prior.velocity.x) / dt,
                y=(velocity.y - prior.velocity.y) / dt,
            )
        points.append(LandmarkMotion(position, velocity, acceleration))
    return HandMotion(tuple(points))
