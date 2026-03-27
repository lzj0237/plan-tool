"""Celery tasks for email sending and reports."""

import logging
from datetime import date, timedelta

from celery import Task
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.email_service import send_daily_summary

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base Celery task with database session support."""

    def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


@DatabaseTask(bind=True)
def send_daily_summary_task(self, task_date: str = None) -> dict:
    """Send daily task summary email.

    Args:
        task_date: Date string in YYYY-MM-DD format (default: today)

    Returns:
        Task result
    """
    try:
        target_date = date.fromisoformat(task_date) if task_date else date.today()

        # Get all tasks
        db = SessionLocal()
        try:
            tasks = db.query(Task).filter(Task.planned_date == target_date).all()

            # Get configuration from environment or defaults
            mail_to = "1607603586@qq.com"  # Default email
            mail_enabled = True

            # TODO: Read from config or database settings

            if mail_enabled:
                # Get SMTP config
                smtp_host = None  # TODO: Get from config
                smtp_port = 587
                username = None  # TODO: Get from config
                password = None  # TODO: Get from config

                # Send email
                success = send_daily_summary(
                    to=mail_to,
                    tasks=tasks,
                    date_str=target_date,
                    smtp_host=smtp_host,
                    smtp_port=smtp_port,
                    username=username,
                    password=password,
                )

                if success:
                    logger.info("Daily summary sent for %s", target_date)
                else:
                    logger.warning("Failed to send daily summary for %s", target_date)
            else:
                logger.info("Email disabled, skipping daily summary")

        finally:
            db.close()

        return {
            "status": "success",
            "date": target_date.isoformat(),
            "tasks_count": len(tasks),
        }

    except Exception as e:
        logger.error("Error sending daily summary: %s", e, exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }


@DatabaseTask(bind=True)
def send_weekly_summary_task(self, week_start: str, week_end: str) -> dict:
    """Send weekly summary report email.

    Args:
        week_start: Start date in YYYY-MM-DD format
        week_end: End date in YYYY-MM-DD format

    Returns:
        Task result
    """
    try:
        from app.services.report_service import generate_weekly_report

        start_date = date.fromisoformat(week_start)
        end_date = date.fromisoformat(week_end)

        db = SessionLocal()
        try:
            mail_to = "1607603586@qq.com"  # Default email
            mail_enabled = True

            # TODO: Read from config or database settings

            if mail_enabled:
                smtp_host = None  # TODO: Get from config
                smtp_port = 587
                username = None  # TODO: Get from config
                password = None  # TODO: Get from config

                # Send weekly report
                success = send_email(
                    to=mail_to,
                    subject=f"📊 周报 {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
                    body="发送周报...",
                    html="<p>周报详情已生成，请查看邮件。</p>",
                    smtp_host=smtp_host,
                    smtp_port=smtp_port,
                    username=username,
                    password=password,
                )

                if success:
                    logger.info("Weekly summary sent for %s - %s", start_date, end_date)
                else:
                    logger.warning("Failed to send weekly summary")
            else:
                logger.info("Email disabled, skipping weekly summary")

        finally:
            db.close()

        return {
            "status": "success",
            "start_date": week_start,
            "end_date": week_end,
        }

    except Exception as e:
        logger.error("Error sending weekly summary: %s", e, exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }
