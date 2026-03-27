"""
任务管理API - 支持多租户和多用户

多租户说明：
- 所有任务都属于某个租户(tenant_id)
- 查询时自动过滤，只返回当前用户有权限看到的数据
- admin角色可以看到租户内所有成员的任务
- member角色只能看到自己创建的任务

认证：
- 大多数端点需要登录，通过 Header: Authorization: Bearer <token>
- 未登录用户无法访问任务API
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Task, TaskExecution
from app.schemas import ExecutionOut, TaskCreate, TaskOut, TaskUpdate
from app.services.task_stats import get_task_time_summary
from app.api.routers.auth import get_current_active_user

router = APIRouter(tags=["tasks"])


def utcnow() -> datetime:
    """获取当前UTC时间"""
    return datetime.now(timezone.utc)


def get_task_or_404(db: Session, task_id: int) -> Task:
    """根据ID获取任务，不存在则抛出404"""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


def check_task_access(db: Session, task: Task, current_user: dict) -> None:
    """
    检查用户是否有权访问指定任务
    
    权限规则：
    - admin角色：可以访问租户内所有任务
    - member角色：只能访问自己创建的任务
    
    Args:
        db: 数据库会话
        task: 要检查的任务
        current_user: 当前用户信息
        
    Raises:
        HTTPException: 无权限访问
    """
    # admin可以访问所有租户内的任务
    if current_user["role"] == "admin":
        return
    
    # member只能访问自己创建的任务
    if task.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="你只能访问自己创建的任务",
        )


@router.post("/tasks", response_model=TaskOut)
def create_task(
    payload: TaskCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    创建新任务
    
    新任务会自动关联到当前用户的租户和用户ID。
    """
    now = utcnow()
    task = Task(
        title=payload.title.strip(),
        description=payload.description,
        planned_date=payload.planned_date,
        planned_start=payload.planned_start,
        planned_end=payload.planned_end,
        planned_duration_minutes=payload.planned_duration_minutes,
        is_fixed=payload.is_fixed,
        status="planned",
        # 多租户支持：自动设置租户ID和用户ID
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
        created_at=now,
        updated_at=now,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    获取任务列表
    
    权限过滤：
    - admin：返回租户内所有成员的任务
    - member：只返回自己创建的任务
    """
    query = db.query(Task)
    
    # 多租户隔离：只查询当前租户的数据
    query = query.filter(Task.tenant_id == current_user["tenant_id"])
    
    # 权限过滤：member只能看自己的任务
    if current_user["role"] != "admin":
        query = query.filter(Task.user_id == current_user["user_id"])
    
    tasks = query.order_by(Task.id.desc()).limit(200).all()
    
    out: list[TaskOut] = []
    for t in tasks:
        summary = get_task_time_summary(db, t.id)
        base = TaskOut.model_validate(t)
        out.append(base.model_copy(update={"total_minutes": summary.total_minutes_ceil}))
    return out


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    获取单个任务的详细信息
    """
    task = get_task_or_404(db, task_id)
    
    # 租户隔离
    if task.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="task not found")
    
    # 权限检查
    check_task_access(db, task, current_user)
    
    summary = get_task_time_summary(db, task_id)
    base = TaskOut.model_validate(task)
    return base.model_copy(update={"total_minutes": summary.total_minutes_ceil})


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int, 
    payload: TaskUpdate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    更新任务信息
    
    注意：status不能直接通过此接口修改，需使用 start/pause/resume/stop 接口。
    """
    task = get_task_or_404(db, task_id)
    
    # 租户隔离
    if task.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="task not found")
    
    # 权限检查
    check_task_access(db, task, current_user)

    data = payload.model_dump(exclude_unset=True)

    # status is controlled by start/pause/resume/stop
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
def delete_task(
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    删除任务
    
    注意：只有任务创建者或租户管理员可以删除。
    """
    task = get_task_or_404(db, task_id)
    
    # 租户隔离
    if task.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="task not found")
    
    # 权限检查：创建者或admin可以删除
    if current_user["role"] != "admin" and task.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="只有任务创建者或管理员可以删除",
        )

    db.delete(task)
    db.commit()
    return {"deleted": True}


def get_open_execution(db: Session, task_id: int) -> TaskExecution | None:
    """获取任务当前未关闭的执行记录"""
    return (
        db.query(TaskExecution)
        .filter(TaskExecution.task_id == task_id, TaskExecution.ended_at.is_(None))
        .order_by(TaskExecution.id.desc())
        .first()
    )


@router.post("/tasks/{task_id}/start", response_model=ExecutionOut)
def start_task(
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    开始执行任务
    
    只有状态为"planned"的任务可以开始。
    """
    task = get_task_or_404(db, task_id)
    
    # 租户隔离
    if task.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="task not found")
    
    # 权限检查
    check_task_access(db, task, current_user)

    if task.status != "planned":
        raise HTTPException(status_code=409, detail="only planned task can be started")

    running = get_open_execution(db, task_id)
    if running:
        raise HTTPException(status_code=409, detail="task already has an open execution")

    ex = TaskExecution(
        task_id=task_id, 
        started_at=utcnow(), 
        ended_at=None, 
        status="running"
    )
    task.status = "running"
    task.updated_at = utcnow()

    db.add(ex)
    db.add(task)
    db.commit()
    db.refresh(ex)
    return ex


@router.post("/tasks/{task_id}/pause", response_model=ExecutionOut)
def pause_task(
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    暂停任务
    
    只有状态为"running"的任务可以暂停。
    """
    task = get_task_or_404(db, task_id)
    
    # 租户隔离
    if task.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="task not found")
    
    # 权限检查
    check_task_access(db, task, current_user)

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
def resume_task(
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    继续执行任务
    
    只有状态为"paused"的任务可以继续。
    """
    task = get_task_or_404(db, task_id)
    
    # 租户隔离
    if task.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="task not found")
    
    # 权限检查
    check_task_access(db, task, current_user)

    if task.status != "paused":
        raise HTTPException(status_code=409, detail="only paused task can be resumed")

    open_ex = get_open_execution(db, task_id)
    if not open_ex or open_ex.status != "paused":
        raise HTTPException(status_code=409, detail="task has no paused execution")

    # Resume by creating a new execution segment
    ex = TaskExecution(
        task_id=task_id, 
        started_at=utcnow(), 
        ended_at=None, 
        status="running"
    )
    task.status = "running"
    task.updated_at = utcnow()

    db.add(ex)
    db.add(task)
    db.commit()
    db.refresh(ex)
    return ex


@router.post("/tasks/{task_id}/stop", response_model=ExecutionOut)
def stop_task(
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    停止任务
    
    将任务标记为完成，并关闭所有未结束的执行记录。
    """
    task = get_task_or_404(db, task_id)
    
    # 租户隔离
    if task.tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=404, detail="task not found")
    
    # 权限检查
    check_task_access(db, task, current_user)

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
