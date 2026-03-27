"""
Tenant model for multi-tenant data isolation.

租户是数据隔离的最小单位。每个租户拥有独立的空间：
- 独立的用户列表
- 独立的任务数据
- 独立的配置

使用场景：
- 免费用户：每个用户自己创建一个租户
- 团队/企业：一个组织创建一个租户，多个成员共享
"""

from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tenant(Base):
    """
    租户模型
    
    Attributes:
        id: 租户唯一标识
        name: 租户名称（如个人姓名或公司名）
        plan: 订阅计划，free=免费版，pro=专业版，enterprise=企业版
        max_members: 最大成员数（-1表示无限制）
        settings: 租户级别的配置（JSON格式存储）
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 租户信息
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 订阅计划
    # free: 基础功能，成员数限制
    # pro: 更多功能，更大成员数
    # enterprise: 无限制，高级功能
    plan: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    
    # 成员限制
    # -1 表示无限制
    max_members: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # 扩展配置（JSON格式）
    # 可以存储如：默认时区、邮件配置、提醒规则等
    settings: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Tenant {self.name} (plan={self.plan})>"
