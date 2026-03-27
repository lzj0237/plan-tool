"""Test email service configuration."""

import os
from datetime import date

# Test configuration
os.environ["DATABASE_URL"] = "postgresql+psycopg://planpilot:planpilot@localhost:5432/planpilot"
os.environ["MAIL_SMTP_HOST"] = "smtp.qq.com"
os.environ["MAIL_SMTP_PORT"] = "587"
os.environ["MAIL_USERNAME"] = "your_email@qq.com"
os.environ["MAIL_PASSWORD"] = "your_smtp_auth_code"

from app.services.email_service import send_email, send_daily_summary, format_task_summary
from app.models import Task, TaskExecution

# Create mock tasks
tasks = [
    Task(
        id=1,
        title="完成PlanPilot v0.3",
        status="done",
        planned_date=date.today(),
        planned_start=None,
        planned_end=None,
        planned_duration_minutes=120,
        is_fixed=False,
        created_at=date.today(),
        updated_at=date.today(),
    ),
    Task(
        id=2,
        title="编写API文档",
        status="running",
        planned_date=date.today(),
        planned_start=None,
        planned_end=None,
        planned_duration_minutes=60,
        is_fixed=False,
        created_at=date.today(),
        updated_at=date.today(),
    ),
    Task(
        id=3,
        title="学习SQLAlchemy",
        status="planned",
        planned_date=date.today(),
        planned_start=None,
        planned_end=None,
        planned_duration_minutes=30,
        is_fixed=False,
        created_at=date.today(),
        updated_at=date.today(),
    ),
]

print("[OK] Email service imported successfully")
print("[OK] Task models imported successfully")

# Test format_task_summary
body, html = format_task_summary(tasks)
print("[OK] Task summary formatted")

print("\n--- Plain Text Preview ---")
print(repr(body[:500]))
print("\n--- HTML Preview ---")
print(repr(html[:500]))

print("\n[OK] All imports successful!")
print("\n[!] To send actual emails, please configure your SMTP settings in .env file")
