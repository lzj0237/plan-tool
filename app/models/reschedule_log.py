from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskRescheduleLog(Base):
    """Records every automatic reschedule (push) applied to a task.

    v0.2 notes:
    - We keep a simple append-only log.
    - `minutes_pushed` can exceed a day when cascading; the task's planned_* fields
      already carry the final computed timestamps.
    """

    __tablename__ = "task_reschedule_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)

    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    from_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    from_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    to_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    to_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    minutes_pushed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
