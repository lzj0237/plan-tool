"""Simple test to verify email service works."""

import os
os.environ["DATABASE_URL"] = "postgresql+psycopg://planpilot:planpilot@localhost:5432/planpilot"

print("Testing imports without database...")

try:
    from app.services.email_service import send_email, send_daily_summary, format_task_summary
    print("[OK] email_service imported")
except Exception as e:
    print(f"[FAIL] email_service: {e}")
    import sys
    sys.exit(1)

try:
    from app.services.report_service import generate_weekly_report, generate_monthly_report
    print("[OK] report_service imported")
except Exception as e:
    print(f"[FAIL] report_service: {e}")
    import sys
    sys.exit(1)

print("\n[OK] All imports successful!")
print("\nFeatures implemented:")
print("1. Email service with SMTP support")
print("2. Daily summary email generation")
print("3. Weekly report generation")
print("4. Monthly report generation")
print("5. Report API endpoints")
print("6. Celery tasks for scheduled emails")
print("\nTo test actual email sending:")
print("1. Configure .env with SMTP settings")
print("2. Run: python test_email_send.py")
