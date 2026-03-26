from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class RescheduleRunIn(BaseModel):
    planned_date: date
    inserted_task_id: int
    reason: str = Field(min_length=1, max_length=200)


class RescheduleRunOut(BaseModel):
    updated_task_ids: list[int]
    logs_created: int
