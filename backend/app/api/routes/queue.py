from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.queue import FlagQueueItem
from app.services import audit_service, dashboard_service

router = APIRouter(prefix="/flags", tags=["flags"])


@router.get("", response_model=list[FlagQueueItem])
def list_flag_queue(
    as_of: date | None = Query(default=None),
    # The query parameter is named "status"; the Python name avoids shadowing the module.
    status_filter: Literal["open", "dismissed"] = Query(default="open", alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor", "administrator")),
) -> list[FlagQueueItem]:
    """The advisor queue across all students. Defaults to open flags for today."""
    rows = dashboard_service.list_flag_queue(db, as_of or date.today(), status_filter)
    audit_service.record(db, user.id, "view", "flag_queue")
    return [
        FlagQueueItem(
            flag_id=flag.id,
            student_id=student.id,
            student_number=student.student_number,
            full_name=student.full_name,
            level=flag.level,
            status=flag.status,
            as_of=flag.as_of,
            factors=flag.factors,
            created_at=flag.created_at,
        )
        for flag, student in rows
    ]