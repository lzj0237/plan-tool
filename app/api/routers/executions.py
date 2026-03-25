from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import TaskExecution
from app.schemas import ExecutionOut

router = APIRouter(tags=["executions"])


@router.get("/tasks/{task_id}/executions", response_model=list[ExecutionOut])
def list_executions(task_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(TaskExecution)
        .filter(TaskExecution.task_id == task_id)
        .order_by(TaskExecution.id.asc())
        .all()
    )
    return rows
