from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.preferences import SchedulingPreferences
from app.models import Task, TaskRescheduleLog


@dataclass(frozen=True)
class RescheduleResult:
    updated_task_ids: list[int]
    logs_created: int


def _day_bounds_utc(d: date) -> tuple[datetime, datetime]:
    """Returns [start, end) bounds for the given date in UTC.

    v0.2 simplification:
    - We store planned_start/planned_end as tz-aware datetimes.
    - For now we treat planned_date as a calendar day in UTC.
      (Later: support user timezone properly.)
    """

    start = datetime.combine(d, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    # half-open interval: [start, end)
    return a_start < b_end and b_start < a_end


def _task_interval_or_none(t: Task) -> tuple[datetime, datetime] | None:
    if not t.planned_start or not t.planned_end:
        return None
    return t.planned_start, t.planned_end


def reschedule_after_insert(
    db: Session,
    *,
    planned_date: date,
    inserted_task_id: int,
    reason: str,
    prefs: SchedulingPreferences | None = None,
) -> RescheduleResult:
    """Cascade-reschedule tasks for a date after inserting/updating a task.

    Business rules (from user):
    1) If push exceeds today's bounds, move to next day.
    2) Minute-level scheduling (no rounding to hours).
    3) If fixed-time tasks are enabled, tasks with is_fixed=True are immovable;
       when we hit them we keep pushing movable tasks further.

    Notes:
    - Only tasks with planned_start+planned_end are considered schedulable.
    - We process tasks in chronological order.
    - We do not change the inserted task (assumed already placed).
    """

    prefs = prefs or SchedulingPreferences()

    day_start, day_end = _day_bounds_utc(planned_date)

    # Pull tasks from this day AND subsequent days because cascading may push
    # beyond the day boundary.
    # v0.2: a conservative window (planned_date .. planned_date+7)
    horizon_end = day_end + timedelta(days=7)

    tasks = (
        db.query(Task)
        .filter(Task.planned_start.is_not(None), Task.planned_end.is_not(None))
        .filter(Task.planned_start >= day_start)
        .filter(Task.planned_start < horizon_end)
        .order_by(Task.planned_start.asc(), Task.id.asc())
        .all()
    )

    # Ensure inserted task is present; if not, still proceed with others.
    inserted = next((t for t in tasks if t.id == inserted_task_id), None)

    updated_ids: list[int] = []
    logs_created = 0

    # Keep a moving cursor of the next free time considering fixed blocks.
    cursor = day_start

    # If inserted task exists and starts after day_start, cursor should be day_start
    # and collisions will handle.

    now = datetime.now(timezone.utc)

    for t in tasks:
        interval = _task_interval_or_none(t)
        if not interval:
            continue

        start, end = interval
        duration = end - start
        if duration.total_seconds() <= 0:
            continue

        # Establish cursor in the same timeline as tasks.
        if start > cursor:
            cursor = start

        # Fixed blocks: they occupy time but cannot be moved.
        if prefs.fixed_time_enabled and t.is_fixed:
            # If cursor is inside fixed block, jump cursor to its end.
            if cursor < end and cursor >= start:
                cursor = end
            # If cursor is before this fixed block, leave it; it will be handled
            # by later movable tasks.
            continue

        # Skip inserted task: treat it as already placed but it still occupies time.
        if inserted and t.id == inserted.id:
            # If cursor overlaps inserted, move cursor to its end.
            if cursor < end and cursor >= start:
                cursor = end
            continue

        # If this task overlaps cursor (cursor is the earliest time we can place),
        # push it to start at cursor.
        if cursor > start:
            new_start = cursor
            new_end = new_start + duration

            # If the push goes beyond the current day end, roll forward to next days.
            # We carry the overflow; minute precision.
            while new_end > day_end:
                overflow = new_end - day_end
                # move to next day
                planned_date = planned_date + timedelta(days=1)
                day_start, day_end = _day_bounds_utc(planned_date)
                new_start = day_start
                new_end = new_start + duration
                # If still too long for a day, keep looping; overflow is naturally handled.

            # Avoid landing inside a fixed block: keep pushing forward until free.
            if prefs.fixed_time_enabled:
                fixed_blocks = [x for x in tasks if x.is_fixed and x.planned_start and x.planned_end]
                changed = True
                while changed:
                    changed = False
                    for fb in fixed_blocks:
                        fb_start, fb_end = fb.planned_start, fb.planned_end
                        if _overlaps(new_start, new_end, fb_start, fb_end):
                            new_start = fb_end
                            new_end = new_start + duration
                            # Crossing day boundary again
                            while new_end > day_end:
                                planned_date = planned_date + timedelta(days=1)
                                day_start, day_end = _day_bounds_utc(planned_date)
                                new_start = day_start
                                new_end = new_start + duration
                            changed = True

            minutes_pushed = int((new_start - start).total_seconds() // 60)

            log = TaskRescheduleLog(
                task_id=t.id,
                reason=reason,
                detail=f"auto push due to conflict after task {inserted_task_id}",
                from_start=start,
                from_end=end,
                to_start=new_start,
                to_end=new_end,
                minutes_pushed=minutes_pushed,
                created_at=now,
            )
            t.planned_start = new_start
            t.planned_end = new_end
            t.planned_date = new_start.date()
            t.updated_at = now

            db.add(log)
            db.add(t)
            updated_ids.append(t.id)
            logs_created += 1

            cursor = new_end
        else:
            cursor = end

    db.commit()

    return RescheduleResult(updated_task_ids=updated_ids, logs_created=logs_created)
