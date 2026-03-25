from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Task, TaskExecution
from app.schemas import ExecutionOut, TaskCreate, TaskOut, TaskUpdate

router = APIRouter(tags=["tasks"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/tasks", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    now = utcnow()
    task = Task(
        title=payload.title.strip(),
        description=payload.description,
        planned_date=payload.planned_date,
        planned_start=payload.planned_start,
        planned_end=payload.planned_end,
        planned_duration_minutes=payload.planned_duration_minutes,
        status="planned",
        created_at=now,
        updated_at=now,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.id.desc()).limit(200).all()
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return get_task_or_404(db, task_id)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(task, k, v)
    task.updated_at = utcnow()

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)
    db.delete(task)
    db.commit()
    return {"deleted": True}


def get_open_execution(db: Session, task_id: int) -> TaskExecution | None:
    return (
        db.query(TaskExecution)
        .filter(TaskExecution.task_id == task_id, TaskExecution.ended_at.is_(None))
        .order_by(TaskExecution.id.desc())
        .first()
    )


@router.post("/tasks/{task_id}/start", response_model=ExecutionOut)
def start_task(task_id: int, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)

    running = get_open_execution(db, task_id)
    if running and running.status == "running":
        raise HTTPException(status_code=409, detail="task already running")
    if running and running.status == "paused":
        # resume: open a new segment
        pass

    ex = TaskExecution(task_id=task_id, started_at=utcnow(), ended_at=None, status="running")
    task.status = "running"
    task.updated_at = utcnow()

    db.add(ex)
    db.add(task)
    db.commit()
    db.refresh(ex)
    return ex


@router.post("/tasks/{task_id}/pause", response_model=ExecutionOut)
def pause_task(task_id: int, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)

    running = get_open_execution(db, task_id)
    if not running or running.status != "running":
        raise HTTPException(status_code=409, detail="task is not running")

    running.status = "paused"
    task.status = "paused"
    task.updated_at = utcnow()

    db.add(running)
    db.add(task)
    db.commit()
    db.refresh(running)
    return running


@router.post("/tasks/{task_id}/stop", response_model=ExecutionOut)
def stop_task(task_id: int, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)

    running = get_open_execution(db, task_id)
    if not running:
        raise HTTPException(status_code=409, detail="task has no open execution")

    running.ended_at = utcnow()
    running.status = "stopped"
    task.status = "done"
    task.updated_at = utcnow()

    db.add(running)
    db.add(task)
    db.commit()
    db.refresh(running)
    return running
