from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import TaskExecution
from app.services.timecalc import TimeSummary, ceil_minutes


def get_task_time_summary(db: Session, task_id: int) -> TimeSummary:
    # Sum finished segments
    finished_seconds = db.query(
        func.coalesce(
            func.sum(
                func.extract("epoch", TaskExecution.ended_at - TaskExecution.started_at)
            ),
            0,
        )
    ).filter(
        TaskExecution.task_id == task_id,
        TaskExecution.ended_at.is_not(None),
    ).scalar()

    total_seconds = int(finished_seconds or 0)
    return TimeSummary(total_seconds=total_seconds, total_minutes_ceil=ceil_minutes(total_seconds))
