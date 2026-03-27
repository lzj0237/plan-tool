"""Test actual email sending."""

import os
from datetime import date

# Configuration
os.environ["MAIL_SMTP_HOST"] = "smtp.qq.com"
os.environ["MAIL_SMTP_PORT"] = "587"
os.environ["MAIL_USERNAME"] = "1607603586@qq.com"
os.environ["MAIL_PASSWORD"] = "YOUR_SMTP_AUTH_CODE"  # Replace with actual auth code
os.environ["MAIL_TO"] = "1607603586@qq.com"
os.environ["MAIL_FROM"] = "PlanPilot <1607603586@qq.com>"

from app.services.email_service import send_email, send_daily_summary, format_task_summary
from app.models import Task

print("Testing email sending...")

# Test daily summary
tasks = [
    Task(
        id=1,
        title="完成PlanPilot v0.3邮件功能",
        status="done",
        planned_date=date(2026, 3, 27),
        planned_start=None,
        planned_end=None,
        planned_duration_minutes=180,
        is_fixed=False,
        created_at=date.today(),
        updated_at=date.today(),
    ),
    Task(
        id=2,
        title="编写测试脚本",
        status="done",
        planned_date=date(2026, 3, 27),
        planned_start=None,
        planned_end=None,
        planned_duration_minutes=120,
        is_fixed=False,
        created_at=date.today(),
        updated_at=date.today(),
    ),
    Task(
        id=3,
        title="文档更新",
        status="running",
        planned_date=date(2026, 3, 27),
        planned_start=None,
        planned_end=None,
        planned_duration_minutes=120,
        is_fixed=False,
        created_at=date.today(),
        updated_at=date.today(),
    ),
]

print("\nGenerating email content...")
body, html = format_task_summary(tasks)

# Save to file instead of printing
with open("email_preview.txt", "w", encoding="utf-8") as f:
    f.write("Plain Text Preview (first 800 chars):\n")
    f.write(body[:800])
    f.write("\n\n")
    f.write("HTML Preview (first 800 chars):\n")
    f.write(html[:800])

print("\nEmail preview saved to email_preview.txt")
print("\n[!] To send actual email, replace 'YOUR_SMTP_AUTH_CODE' with real QQ mail authorization code")
print("[!] Also ensure .env file is configured with correct SMTP settings")
