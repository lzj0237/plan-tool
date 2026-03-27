"""
认证服务 - 处理用户登录、注册、密码验证等

使用JWT(JSON Web Token)实现无状态认证：
1. 用户登录时验证密码，生成access token返回
2. 后续请求通过token验证身份，无需存储session
3. Token有过期时间，过期后需要重新登录

密码安全：
- 使用bcrypt算法哈希密码
- 永远不在数据库中存储明文密码
- 验证时比较哈希值
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import secrets

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.tenant import Tenant

# 简单的密码哈希函数（用于开发环境）
# 生产环境应使用bcrypt，这里简化处理
def simple_hash(password: str, salt: str = None) -> tuple[str, str]:
    """简单的SHA256哈希"""
    if salt is None:
        salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return hash_obj.hexdigest() + ':' + salt, salt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        parts = hashed_password.split(':')
        if len(parts) != 2:
            return False
        actual_hash, salt = parts
        test_hash, _ = simple_hash(plain_password, salt)
        # test_hash的格式是 "hash:salt"，我们需要只比较hash部分
        return actual_hash == test_hash.split(':')[0]
    except:
        return False

def get_password_hash(password: str) -> str:
    """哈希密码"""
    hashed, salt = simple_hash(password)
    return hashed

# JWT配置
ALGORITHM = "HS256"  # HMAC-SHA256，对称签名算法
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes  # token有效期（分钟）


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码到token中的数据（应包含user_id, tenant_id等）
        expires_delta: token过期时间，不提供则使用默认配置
        
    Returns:
        JWT token字符串
    """
    to_encode = data.copy()
    
    # 计算过期时间
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 在token数据中加入过期时间
    to_encode.update({"exp": expire})
    
    # 使用HS256算法签名，SECRET_KEY是密钥
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码并验证JWT token
    
    Args:
        token: JWT token字符串
        
    Returns:
        解码后的数据字典，token无效返回None
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # token过期、签名错误、格式错误等都会进入这里
        return None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    验证用户登录
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        password: 明文密码
        
    Returns:
        验证成功返回User对象，失败返回None
    """
    # 查找用户
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # 用户不存在
        return None
    
    if not verify_password(password, user.hashed_password):
        # 密码错误
        return None
    
    if not user.is_active:
        # 账号已禁用
        return None
    
    return user


def create_user_with_tenant(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    tenant_name: Optional[str] = None
) -> tuple[User, Tenant]:
    """
    创建新用户，并为其创建独立的租户
    
    这是最常见的场景：每个新用户获得自己的私人空间。
    
    Args:
        db: 数据库会话
        email: 用户邮箱（登录账号）
        password: 明文密码
        full_name: 用户显示名称
        tenant_name: 租户名称，默认使用用户名称
        
    Returns:
        tuple[User, Tenant]: 新创建的用户和租户对象
    """
    # 创建租户（个人用户，限制1个成员）
    now = datetime.now(timezone.utc)
    tenant = Tenant(
        name=tenant_name or f"{full_name}的租户",
        plan="free",
        max_members=1,
        created_at=now,
        updated_at=now,
    )
    db.add(tenant)
    db.flush()  # 获取tenant.id

    # 创建用户
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        tenant_id=tenant.id,
        is_active=True,
        role="admin",  # 个人用户，自动成为租户管理员
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user, tenant


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()
