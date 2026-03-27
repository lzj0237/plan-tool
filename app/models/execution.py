from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskExecution(Base):
    """
    任务执行记录模型 - 记录每次时间追踪的起止
    
    用于追踪任务的实际执行时间：
    - 一个任务可以有多次执行记录（开始→暂停→继续→结束）
    - 通过 started_at 和 ended_at 计算实际耗时
    - 所有时间都是UTC时间，带时区信息
    
    Attributes:
        id: 执行记录唯一标识
        task_id: 关联的任务ID
        
        started_at: 本次执行开始时间
        ended_at: 本次执行结束时间（None表示仍在执行中）
        
        status: 执行状态
            - running: 执行中
            - paused: 已暂停（暂停时 ended_at 被设置）
            - completed: 已完成（正常结束）
    """
    
    __tablename__ = "task_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联的任务ID
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )

    # 执行时间
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 执行状态
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running", index=True)
