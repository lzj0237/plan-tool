from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class TimeSummary:
    total_seconds: int
    total_minutes_ceil: int


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def seconds_between(start: datetime, end: datetime) -> int:
    delta = end - start
    seconds = int(delta.total_seconds())
    return max(0, seconds)


def ceil_minutes(total_seconds: int) -> int:
    if total_seconds <= 0:
        return 0
    return (total_seconds + 59) // 60
