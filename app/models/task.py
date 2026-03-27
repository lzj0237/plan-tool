from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Task(Base):
    """
    任务模型 - 支持多租户和多用户
    
    多租户说明：
    - 每个任务属于一个租户(tenant_id)，通过租户隔离实现数据安全
    - admin角色的用户可以看到租户内所有成员的任务
    - member角色的用户只能看到自己的任务
    
    Attributes:
        id: 任务唯一标识
        tenant_id: 所属租户ID，用于数据隔离
        user_id: 创建者用户ID
        
        title: 任务标题
        description: 任务详细描述
        
        planned_date: 计划执行日期
        planned_start: 计划开始时间
        planned_end: 计划结束时间
        planned_duration_minutes: 预计时长（分钟）
        
        is_fixed: 是否为固定时间段任务（顺延时不可移动）
        
        status: 任务状态
            - planned: 已计划，未开始
            - running: 执行中
            - paused: 已暂停
            - done: 已完成
            
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ===== 多租户支持 =====
    # 租户ID：用于数据隔离，所有查询默认基于此字段过滤
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # 创建者ID：记录任务归属（方便权限判断）
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )

    # ===== 任务内容 =====
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ===== 计划时间 =====
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    planned_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ===== 顺延规则 =====
    # 固定时间段任务在自动顺延时不会被移动
    is_fixed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ===== 状态 =====
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned", index=True)

    # ===== 时间戳 =====
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
