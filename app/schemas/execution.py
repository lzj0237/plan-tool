from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

ExecutionStatus = Literal["running", "paused", "stopped"]


class ExecutionOut(BaseModel):
    id: int
    task_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: ExecutionStatus

    model_config = {"from_attributes": True}
