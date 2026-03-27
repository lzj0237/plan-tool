"""
User model for multi-tenant support.

每个用户属于一个租户(tenant)，租户之间数据完全隔离。
用户可以拥有不同的角色(默认都是member)。

典型的多租户场景：
- 个人用户：每个用户自己是一个租户
- 团队用户：多个用户共享一个租户（团队）
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """
    用户模型
    
    Attributes:
        id: 用户唯一标识
        email: 用户邮箱（登录账号），同一租户内必须唯一
        hashed_password: 密码的哈希值（永远不要存储明文密码）
        full_name: 用户显示名称
        tenant_id: 所属租户ID，租户内的所有用户共享这个ID
        is_active: 账号是否启用，禁用后无法登录
        is_superuser: 是否为超级用户（可管理所有租户）
        role: 用户角色，member=普通成员，admin=租户管理员
        created_at: 账号创建时间
        updated_at: 最后更新时间
    """
    
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 登录凭证
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 用户信息
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 多租户支持
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # 账号状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 角色权限
    # member: 普通成员，只能操作自己的任务
    # admin: 租户管理员，可以管理租户内的所有任务和成员
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    def __repr__(self) -> str:
        return f"<User {self.email} (tenant={self.tenant_id}, role={self.role})>"
