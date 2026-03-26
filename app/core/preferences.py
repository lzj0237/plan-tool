from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SchedulingPreferences:
    """User-tunable scheduling preferences.

    v0.2 scope:
    - We keep this simple and in-process.
    - Later (v0.5) it can be persisted per user/tenant.
    """

    # Whether the user uses fixed-time tasks ("busy blocks").
    # If True, the rescheduler will treat tasks with is_fixed=True as immovable.
    fixed_time_enabled: bool = True
