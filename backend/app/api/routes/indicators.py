from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles, student_scope
from app.db.session import get_db
from app.models.user import User
from app.schemas.indicator import IndicatorsRead
from app.services import audit_service, indicators as indicator_service
from app.services.indicators import StudentNotFoundError

router = APIRouter(prefix="/students/{student_id}/indicators", tags=["indicators"])


@router.get("", response_model=IndicatorsRead, dependencies=[Depends(student_scope)])
def get_indicators(
    student_id: int,
    as_of: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor", "administrator", "lecturer")),
) -> IndicatorsRead:
    """Return the indicators for a student the user is allowed to see."""
    try:
        result = indicator_service.calculate_indicators(db, student_id, as_of or date.today())
    except StudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_service.record(db, user.id, "view", "indicators", student_id=student_id)
    return result