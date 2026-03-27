"""Simple test to verify imports work."""

import os
os.environ["DATABASE_URL"] = "postgresql+psycopg://planpilot:planpilot@localhost:5432/planpilot"

print("Testing imports...")

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

try:
    from app.api.routers import reports
    print("[OK] reports router imported")
except Exception as e:
    print(f"[FAIL] reports router: {e}")
    import sys
    sys.exit(1)

try:
    from app.tasks import email_tasks
    print("[OK] email_tasks imported")
except Exception as e:
    print(f"[FAIL] email_tasks: {e}")
    import sys
    sys.exit(1)

print("\nAll imports successful!")
print("\nYou can now:")
print("1. Configure email settings in .env file")
print("2. Run 'docker compose up -d' to start services")
print("3. Check API docs at http://localhost:8000/docs")
