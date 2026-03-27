"""Report generation service for weekly and monthly summaries."""

from datetime import datetime, date, timedelta
from typing import Optional
import logging

from sqlalchemy.orm import Session
from app.models import Task, TaskExecution
from app.services.email_service import send_email

logger = logging.getLogger(__name__)


def get_task_summary(
    db: Session,
    start_date: date,
    end_date: date,
) -> dict:
    """Generate a summary of tasks for a date range.

    Args:
        db: Database session
        start_date: Start date of the range
        end_date: End date of the range

    Returns:
        Dictionary with summary statistics
    """
    # Get all tasks in the date range
    tasks = db.query(Task).filter(
        Task.planned_date >= start_date,
        Task.planned_date <= end_date,
    ).all()

    # Group by status
    status_counts = {
        "planned": 0,
        "running": 0,
        "paused": 0,
        "done": 0,
    }

    # Group by completion status
    completed_tasks = []
    pending_tasks = []

    for task in tasks:
        status_emoji = {
            "planned": "📋",
            "running": "🚀",
            "paused": "⏸️",
            "done": "✅",
        }.get(task.status, "❓")

        if task.status == "done":
            completed_tasks.append((task, status_emoji))
        else:
            pending_tasks.append((task, status_emoji))

        if task.status in status_counts:
            status_counts[task.status] += 1
        else:
            status_counts[task.status] = 1

    # Calculate total planned time
    total_planned_minutes = sum(t.planned_duration_minutes or 0 for t in tasks)

    # Get all executions and calculate actual time
    all_executions = db.query(TaskExecution).filter(
        TaskExecution.started_at >= datetime.combine(start_date, datetime.min.time()),
        TaskExecution.started_at <= datetime.combine(end_date + timedelta(days=1), datetime.min.time()),
    ).all()

    # Group by task
    exec_by_task: dict[int, list[TaskExecution]] = {}
    for exec in all_executions:
        if exec.task_id not in exec_by_task:
            exec_by_task[exec.task_id] = []
        exec_by_task[exec.task_id].append(exec)

    # Calculate actual time per task
    actual_minutes_by_task: dict[int, int] = {}
    for task_id, executions in exec_by_task.items():
        total = 0
        for exec in executions:
            if exec.ended_at:
                duration = exec.ended_at - exec.started_at
                total += int(duration.total_seconds() / 60)
        actual_minutes_by_task[task_id] = total

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_tasks": len(tasks),
        "completed_tasks": len(completed_tasks),
        "pending_tasks": len(pending_tasks),
        "status_counts": status_counts,
        "total_planned_minutes": total_planned_minutes,
        "completed_tasks_list": completed_tasks,
        "pending_tasks_list": pending_tasks,
        "actual_minutes_by_task": actual_minutes_by_task,
    }


def generate_weekly_report(
    db: Session,
    week_start: date,
    week_end: date,
    email_to: Optional[str] = None,
    subject: Optional[str] = None,
) -> dict:
    """Generate a weekly summary report.

    Args:
        db: Database session
        week_start: First day of the week
        week_end: Last day of the week
        email_to: Email address to send the report to (optional)
        subject: Custom subject line (optional)

    Returns:
        Report summary
    """
    summary = get_task_summary(db, week_start, week_end)

    # Generate report body
    days = []
    for day in (week_start + timedelta(days=i) for i in range((week_end - week_start).days + 1)):
        day_tasks = [t for t in summary["completed_tasks_list"] + summary["pending_tasks_list"] if t[0].planned_date == day]
        day_summary = {
            "date": day,
            "tasks": day_tasks,
        }
        days.append(day_summary)

    # Build message
    report_title = subject or f"📊 {week_start.strftime('%Y年%m月%d日')} - {week_end.strftime('%Y年%m月%d日')} 周报"

    plain_body = f"{report_title}\n\n"
    html_body = f"<h1>{report_title}</h1>\n\n"

    for day in days:
        day_str = day["date"].strftime('%Y-%m-%d (周%a)')
        plain_body += f"--- {day_str} ---\n"
        html_body += f"<h3>{day_str}</h3>\n"

        if not day["tasks"]:
            plain_body += "  无任务\n\n"
            html_body += "<ul><li>无任务</li></ul>\n\n"
            continue

        for task, emoji in day["tasks"]:
            plain_body += f"  {emoji} {task.title}\n"
            html_body += f"<li>{emoji} {task.title}</li>\n"

        plain_body += "\n"
        html_body += "<ul>\n"

    # Add summary statistics
    plain_body += "\n--- 统计 ---\n"
    plain_body += f"总任务数: {summary['total_tasks']}\n"
    plain_body += f"已完成: {summary['completed_tasks']}\n"
    plain_body += f"待处理: {summary['pending_tasks']}\n"
    plain_body += f"预计总时长: {summary['total_planned_minutes']} 分钟\n"

    html_body += "<hr>\n<h3>统计</h3>\n"
    html_body += f"<p>总任务数: {summary['total_tasks']}</p>\n"
    html_body += f"<p>已完成: {summary['completed_tasks']}</p>\n"
    html_body += f"<p>待处理: {summary['pending_tasks']}</p>\n"
    html_body += f"<p>预计总时长: {summary['total_planned_minutes']} 分钟</p>\n"

    # Send via email if requested
    if email_to:
        send_email(
            to=email_to,
            subject=subject or f"周报 {week_start.strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}",
            body=plain_body,
            html=html_body,
        )

    return summary


def generate_monthly_report(
    db: Session,
    month: date,
    email_to: Optional[str] = None,
    subject: Optional[str] = None,
) -> dict:
    """Generate a monthly summary report.

    Args:
        db: Database session
        month: Month to report on
        email_to: Email address to send the report to (optional)
        subject: Custom subject line (optional)

    Returns:
        Report summary
    """
    year = month.year
    month_num = month.month

    first_day = date(year, month_num, 1)
    last_day = date(year, month_num, 28)  # Will be adjusted if month has more days

    # Adjust end day to actual month end
    if month_num == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month_num + 1, 1)

    last_day = next_month - timedelta(days=1)

    return generate_weekly_report(
        db,
        week_start=first_day,
        week_end=last_day,
        email_to=email_to,
        subject=subject or f"📈 {year}年{month_num}月 报告",
    )
