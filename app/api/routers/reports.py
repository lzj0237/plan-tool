"""Report generation API endpoints."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Task
from app.services.report_service import generate_monthly_report, generate_weekly_report

router = APIRouter(tags=["reports"])


@router.get("/reports/summary")
def get_task_summary(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
) -> dict:
    """Get a summary of tasks for a date range.

    Args:
        start_date: Start date of the range
        end_date: End date of the range

    Returns:
        Task summary statistics
    """
    return get_task_summary(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/reports/weekly")
def generate_weekly_report_api(
    week_start: date,
    week_end: date,
    email_to: Optional[str] = None,
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Generate and optionally send a weekly report.

    Args:
        week_start: First day of the week
        week_end: Last day of the week
        email_to: Email address to send the report to
        subject: Custom subject line (optional)

    Returns:
        Report summary
    """
    if week_end < week_start:
        raise HTTPException(status_code=400, detail="week_end must be >= week_start")

    # Send email if requested
    if email_to:
        report = generate_weekly_report(
            db=db,
            week_start=week_start,
            week_end=week_end,
            email_to=email_to,
            subject=subject,
        )
    else:
        report = generate_weekly_report(
            db=db,
            week_start=week_start,
            week_end=week_end,
            email_to=None,
            subject=subject,
        )

    return report


@router.get("/reports/monthly")
def generate_monthly_report_api(
    month: date,
    email_to: Optional[str] = None,
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Generate and optionally send a monthly report.

    Args:
        month: Month to report on
        email_to: Email address to send the report to
        subject: Custom subject line (optional)

    Returns:
        Report summary
    """
    report = generate_monthly_report(
        db=db,
        month=month,
        email_to=email_to,
        subject=subject,
    )

    return report
