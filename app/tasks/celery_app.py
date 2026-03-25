from celery import Celery

from app.core.config import settings

celery = Celery(
    "planpilot",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.conf.timezone = settings.timezone
