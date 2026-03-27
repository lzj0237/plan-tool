from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置
    
    所有配置从环境变量或.env文件读取。
    配置分为几类：
    - DB: 数据库连接
    - App: 应用基础信息
    - Security: JWT密钥和Token配置
    - Email: 邮件发送配置
    - Task: 任务默认行为配置
    """
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore",  # 忽略未定义的变量
        case_sensitive=False,  # 环境变量不区分大小写
    )

    # ===== 数据库 =====
    database_url: str = "postgresql+psycopg2://planpilot:planpilot@localhost:5432/planpilot"

    # ===== Redis（Celery用） =====
    redis_url: str = "redis://localhost:6379/0"

    # ===== 应用基础 =====
    app_name: str = "PlanPilot"
    timezone: str = "Asia/Shanghai"

    # ===== 安全认证 =====
    # JWT密钥，生产环境必须使用复杂的随机字符串
    secret_key: str = "change-me-in-production"
    
    # Token过期时间（分钟），默认7天
    access_token_expire_minutes: int = 10080

    # ===== 邮件配置 =====
    mail_enabled: bool = False
    mail_to: str = ""
    mail_from: str = ""
    mail_smtp_host: str = ""
    mail_smtp_port: int = 587
    mail_username: str = ""
    mail_password: str = ""

    # ===== 任务默认行为 =====
    default_window_start: str = "20:00"  # 默认计划开始时间
    default_window_end: str = "22:00"    # 默认计划结束时间
    default_delay_reason: str = "事太多，没时间执行"  # 默认顺延原因


settings = Settings()
