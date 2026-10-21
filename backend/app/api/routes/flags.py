from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles, student_scope
from app.db.session import get_db
from app.models.user import User
from app.schemas.flag import FlagDismiss, FlagRead
from app.services import audit_service, flag_service
from app.services.flag_service import FlagAlreadyDismissedError, FlagNotFoundError
from app.services.indicators import StudentNotFoundError

router = APIRouter(tags=["flags"])


@router.post("/students/{student_id}/flags/evaluate", response_model=FlagRead | None)
def evaluate_flag(
    student_id: int,
    as_of: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor")),
) -> FlagRead | None:
    """Evaluate a student and store a flag if a rule fires. Advisors only."""
    try:
        flag = flag_service.evaluate_student(db, student_id, as_of or date.today())
    except StudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_service.record(
        db, user.id, "evaluate", "flag",
        resource_id=flag.id if flag else None, student_id=student_id,
    )
    return flag


@router.get(
    "/students/{student_id}/flags",
    response_model=list[FlagRead],
    dependencies=[Depends(student_scope)],
)
def list_flags(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor", "administrator", "lecturer")),
) -> list[FlagRead]:
    """List a student's flags for users who can see that student."""
    try:
        flags = flag_service.list_flags(db, student_id)
    except StudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_service.record(db, user.id, "view", "flags", student_id=student_id)
    return flags


@router.post("/flags/{flag_id}/dismiss", response_model=FlagRead)
def dismiss_flag(
    flag_id: int,
    payload: FlagDismiss,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor")),
) -> FlagRead:
    """Dismiss a flag with a reason. Advisors only."""
    try:
        flag = flag_service.dismiss_flag(db, flag_id, payload.reason)
    except FlagNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FlagAlreadyDismissedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    audit_service.record(
        db, user.id, "dismiss", "flag",
        resource_id=flag_id, student_id=flag.student_id,
    )
    return flag