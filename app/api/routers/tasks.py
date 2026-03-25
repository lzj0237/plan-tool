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

    # status is controlled by start/pause/resume/stop in v0.1
    if "status" in data:
        raise HTTPException(status_code=400, detail="status cannot be updated directly")

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

    if task.status != "planned":
        raise HTTPException(status_code=409, detail="only planned task can be started")

    running = get_open_execution(db, task_id)
    if running:
        raise HTTPException(status_code=409, detail="task already has an open execution")

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

    if task.status != "running":
        raise HTTPException(status_code=409, detail="only running task can be paused")

    running = get_open_execution(db, task_id)
    if not running or running.status != "running":
        raise HTTPException(status_code=409, detail="task has no running execution")

    running.status = "paused"
    task.status = "paused"
    task.updated_at = utcnow()

    db.add(running)
    db.add(task)
    db.commit()
    db.refresh(running)
    return running


@router.post("/tasks/{task_id}/resume", response_model=ExecutionOut)
def resume_task(task_id: int, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)

    if task.status != "paused":
        raise HTTPException(status_code=409, detail="only paused task can be resumed")

    open_ex = get_open_execution(db, task_id)
    if not open_ex or open_ex.status != "paused":
        raise HTTPException(status_code=409, detail="task has no paused execution")

    # Resume by creating a new execution segment
    ex = TaskExecution(task_id=task_id, started_at=utcnow(), ended_at=None, status="running")
    task.status = "running"
    task.updated_at = utcnow()

    db.add(ex)
    db.add(task)
    db.commit()
    db.refresh(ex)
    return ex


@router.post("/tasks/{task_id}/stop", response_model=ExecutionOut)
def stop_task(task_id: int, db: Session = Depends(get_db)):
    task = get_task_or_404(db, task_id)

    if task.status not in ("running", "paused"):
        raise HTTPException(status_code=409, detail="only running/paused task can be stopped")

    open_ex = get_open_execution(db, task_id)
    if not open_ex:
        raise HTTPException(status_code=409, detail="task has no open execution")

    open_ex.ended_at = utcnow()
    open_ex.status = "stopped"
    task.status = "done"
    task.updated_at = utcnow()

    db.add(open_ex)
    db.add(task)
    db.commit()
    db.refresh(open_ex)
    return open_ex
