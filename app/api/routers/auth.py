"""
认证API - 处理用户登录、注册、Token验证等

Endpoints:
- POST /api/auth/register - 用户注册
- POST /api/auth/login - 用户登录
- GET /api/auth/me - 获取当前用户信息

使用JWT Bearer Token认证：
1. 登录成功后获得access_token
2. 后续请求在Header中携带: Authorization: Bearer <token>
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserOut,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user_with_tenant,
    decode_access_token,
    get_user_by_id,
)

router = APIRouter(tags=["auth"])

# OAuth2 scheme，用于从请求Header中提取token
# 客户端需要使用: Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    从token中解析并验证当前用户
    
    这是一个依赖注入函数，FastAPI会自动：
    1. 从请求Header中提取Bearer token
    2. 解码并验证token
    3. 提取用户信息（user_id, tenant_id, role）
    
    Args:
        token: JWT token字符串
        
    Returns:
        包含用户信息的字典
        
    Raises:
        HTTPException: token无效或已过期
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # 从token中提取用户信息
    user_id: int = payload.get("sub")
    tenant_id: int = payload.get("tenant_id")
    role: str = payload.get("role")
    
    if user_id is None or tenant_id is None:
        raise credentials_exception
    
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": role,
    }


def get_current_active_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    验证当前用户是否有效（账号未被禁用）
    
    在get_current_user之后调用，进一步检查用户状态。
    """
    user = get_user_by_id(db, user_id=current_user["user_id"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )
    return current_user


@router.post("/register", response_model=RegisterResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册
    
    每个新用户会获得：
    1. 一个独立的租户（私人空间）
    2. 租户管理员角色（admin）
    
    注册后自动登录，返回access_token。
    """
    # 检查邮箱是否已被注册
    from app.services.auth_service import get_user_by_email
    existing = get_user_by_email(db, email=request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )
    
    # 创建用户和租户
    user, tenant = create_user_with_tenant(
        db=db,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        tenant_name=request.tenant_name,
    )
    
    return RegisterResponse(
        user_id=user.id,
        tenant_id=tenant.id,
        email=user.email,
        full_name=user.full_name,
        message="注册成功",
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录
    
    验证邮箱密码，成功后返回JWT access_token。
    客户端需要在后续请求的Header中携带此token:
    Authorization: Bearer <access_token>
    """
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成JWT token，包含用户身份信息
    access_token = create_access_token(
        data={
            "sub": user.id,           # 用户ID
            "tenant_id": user.tenant_id,  # 租户ID
            "role": user.role,        # 用户角色
        }
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        tenant_id=user.tenant_id,
        full_name=user.full_name,
        role=user.role,
    )


@router.get("/me", response_model=UserOut)
def get_me(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取当前登录用户的信息
    
    需要在请求Header中携带有效的access_token。
    """
    user = get_user_by_id(db, user_id=current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user
