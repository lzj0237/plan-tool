from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import RescheduleRunIn, RescheduleRunOut
from app.services.rescheduler import reschedule_after_insert

router = APIRouter(tags=["reschedule"])


@router.post("/reschedule/run", response_model=RescheduleRunOut)
def run_reschedule(payload: RescheduleRunIn, db: Session = Depends(get_db)):
    result = reschedule_after_insert(
        db,
        planned_date=payload.planned_date,
        inserted_task_id=payload.inserted_task_id,
        reason=payload.reason,
    )
    return RescheduleRunOut(updated_task_ids=result.updated_task_ids, logs_created=result.logs_created)
