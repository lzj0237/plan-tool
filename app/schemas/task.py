from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

TaskStatus = Literal["planned", "running", "paused", "done"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None

    planned_date: Optional[date] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    planned_duration_minutes: Optional[int] = Field(default=None, ge=1)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None

    planned_date: Optional[date] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    planned_duration_minutes: Optional[int] = Field(default=None, ge=1)

    status: Optional[TaskStatus] = None


class TaskOut(BaseModel):
    id: int
    title: str
    status: TaskStatus

    description: Optional[str] = None
    planned_date: Optional[date] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    planned_duration_minutes: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
