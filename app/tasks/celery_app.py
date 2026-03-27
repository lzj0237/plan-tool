from celery import Celery

from app.core.config import settings

celery = Celery(
    "planpilot",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.conf.timezone = settings.timezone

# Import tasks to register them
from app.tasks.email_tasks import send_daily_summary_task, send_weekly_summary_task
celery.task(name="email.send_daily_summary", bind=True)(send_daily_summary_task)
celery.task(name="email.send_weekly_summary", bind=True)(send_weekly_summary_task)
