"""
认证相关的请求/响应模型

使用Pydantic进行数据验证，确保API接收到的数据符合预期格式。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ===== 登录 =====

class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=1, description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="JWT访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user_id: int = Field(..., description="用户ID")
    tenant_id: int = Field(..., description="租户ID")
    full_name: str = Field(..., description="用户名称")
    role: str = Field(..., description="用户角色")


# ===== 注册 =====

class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr = Field(..., description="用户邮箱（登录账号）")
    password: str = Field(..., min_length=6, max_length=100, description="密码（至少6位）")
    full_name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    tenant_name: Optional[str] = Field(None, max_length=100, description="租户名称（可选）")


class RegisterResponse(BaseModel):
    """注册响应"""
    user_id: int = Field(..., description="用户ID")
    tenant_id: int = Field(..., description="租户ID")
    email: str = Field(..., description="用户邮箱")
    full_name: str = Field(..., description="用户名称")
    message: str = Field(default="注册成功", description="提示信息")


# ===== 用户信息 =====

class UserOut(BaseModel):
    """用户信息输出"""
    id: int
    email: str
    full_name: str
    tenant_id: int
    role: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===== Token验证 =====

class TokenPayload(BaseModel):
    """JWT token载荷"""
    sub: Optional[int] = Field(None, description="用户ID")
    tenant_id: Optional[int] = Field(None, description="租户ID")
    role: Optional[str] = Field(None, description="用户角色")
    exp: Optional[datetime] = Field(None, description="过期时间")
