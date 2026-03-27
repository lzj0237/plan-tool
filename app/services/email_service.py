"""Email service for sending reminders and reports."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, date
import logging

from app.core.config import settings
from app.models import Task, TaskExecution

logger = logging.getLogger(__name__)


def send_email(
    to: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: int = 587,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> bool:
    """Send an email.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text body
        html: HTML body (optional)
        smtp_host: SMTP server host (default from settings)
        smtp_port: SMTP port (default 587)
        username: SMTP username (default from settings)
        password: SMTP password (default from settings)

    Returns:
        True if successful, False otherwise
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.mail_from or settings.app_name
    msg["To"] = to

    # Attach plain text version
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Attach HTML version if provided
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        # Use provided credentials or fall back to settings
        host = smtp_host or settings.mail_smtp_host
        port = smtp_port
        user = username or settings.mail_username
        pwd = password or settings.mail_password

        if not host or not user or not pwd:
            logger.error("SMTP configuration incomplete: host=%s, username=%s", host, user)
            return False

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, pwd)
            server.send_message(msg)
        logger.info("Email sent to %s", to)
        return True

    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False


def format_task_summary(tasks: list[Task]) -> tuple[str, str]:
    """Format tasks as a summary message.

    Args:
        tasks: List of tasks

    Returns:
        Tuple of (plain text body, HTML body)
    """
    if not tasks:
        return (
            "今天没有计划任务。",
            "<p>今天没有计划任务。</p>",
        )

    plain_lines = []
    html_lines = ["<ul>"]

    for task in tasks:
        status_emoji = {
            "planned": "📋",
            "running": "🚀",
            "paused": "⏸️",
            "done": "✅",
        }.get(task.status, "❓")

        plain_lines.append(f"{status_emoji} {task.title}")
        if task.planned_start and task.planned_end:
            plain_lines.append(f"   时间: {task.planned_start.strftime('%H:%M')} - {task.planned_end.strftime('%H:%M')}")
        elif task.planned_duration_minutes:
            plain_lines.append(f"   预计时长: {task.planned_duration_minutes} 分钟")

        plain_lines.append("")
        html_lines.append(f"    <li>{status_emoji} {task.title}</li>")

    plain_lines.append("")
    html_lines.append("</ul>")

    return (
        "\n".join(plain_lines),
        "\n".join(html_lines),
    )


def send_daily_summary(
    to: str,
    tasks: list[Task],
    date_str: Optional[date] = None,
    smtp_host: Optional[str] = None,
    smtp_port: int = 587,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> bool:
    """Send daily task summary email.

    Args:
        to: Recipient email
        tasks: List of tasks for the day
        date_str: Date string in YYYY-MM-DD format (default: today)
        smtp_host: SMTP host override
        smtp_port: SMTP port override
        username: SMTP username override
        password: SMTP password override

    Returns:
        True if successful, False otherwise
    """
    target_date = date_str or date.today()
    subject = f"📅 {target_date} 任务清单"

    # Filter tasks for the specified date (exact match or today)
    today_tasks = [t for t in tasks if t.planned_date == target_date]

    body, html = format_task_summary(today_tasks)

    # Add footer
    footer = (
        "\n\n---\n"
        f"PlanPilot - 个人任务管理工具\n"
        f"查看详情: http://localhost:8000/api/tasks"
    )
    html_footer = "<br><br><hr><p>PlanPilot - 个人任务管理工具<br>查看详情: <a href='http://localhost:8000/api/tasks'>任务列表</a></p>"

    full_body = body + footer
    full_html = html + html_footer if html else body + html_footer

    return send_email(
        to=to,
        subject=subject,
        body=full_body,
        html=full_html,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        username=username,
        password=password,
    )
