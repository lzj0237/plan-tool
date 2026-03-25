from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Task, TaskExecution

router = APIRouter(tags=["tasks"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/tasks")
def create_task(payload: dict, db: Session = Depends(get_db)):
    title = (payload.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    now = utcnow()
    task = Task(
        title=title,
        description=payload.get("description"),
        planned_date=payload.get("planned_date"),
        planned_start=payload.get("planned_start"),
        planned_end=payload.get("planned_end"),
        planned_duration_minutes=payload.get("planned_duration_minutes"),
        status=payload.get("status") or "planned",
        created_at=now,
        updated_at=now,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "title": task.title, "status": task.status}


@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.id.desc()).limit(200).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "planned_date": t.planned_date,
            "planned_start": t.planned_start,
            "planned_end": t.planned_end,
            "planned_duration_minutes": t.planned_duration_minutes,
        }
        for t in tasks
    ]


@router.post("/tasks/{task_id}/start")
def start_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")

    running = (
        db.query(TaskExecution)
        .filter(TaskExecution.task_id == task_id, TaskExecution.ended_at.is_(None))
        .first()
    )
    if running:
        raise HTTPException(status_code=409, detail="task already running")

    ex = TaskExecution(task_id=task_id, started_at=utcnow(), ended_at=None, status="running")
    task.status = "running"
    task.updated_at = utcnow()

    db.add(ex)
    db.add(task)
    db.commit()
    db.refresh(ex)
    return {"execution_id": ex.id, "task_id": task_id, "started_at": ex.started_at}


@router.post("/tasks/{task_id}/stop")
def stop_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")

    running = (
        db.query(TaskExecution)
        .filter(TaskExecution.task_id == task_id, TaskExecution.ended_at.is_(None))
        .order_by(TaskExecution.id.desc())
        .first()
    )
    if not running:
        raise HTTPException(status_code=409, detail="task is not running")

    running.ended_at = utcnow()
    running.status = "stopped"
    task.status = "done"
    task.updated_at = utcnow()

    db.add(running)
    db.add(task)
    db.commit()

    return {"execution_id": running.id, "task_id": task_id, "ended_at": running.ended_at}
