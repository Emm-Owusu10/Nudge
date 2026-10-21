from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.indicator import IndicatorsRead
from app.schemas.intervention import (
    FollowUpRead,
    InterventionCreate,
    InterventionRead,
    OutcomeUpdate,
)
from app.services import audit_service, intervention_service
from app.services.indicators import StudentNotFoundError
from app.services.intervention_service import (
    FlagNotForStudentError,
    InterventionNotFoundError,
)

router = APIRouter(tags=["interventions"])


@router.post(
    "/students/{student_id}/interventions",
    response_model=InterventionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_intervention(
    student_id: int,
    payload: InterventionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor")),
) -> InterventionRead:
    """Record an intervention. Advisors only."""
    try:
        intervention = intervention_service.create_intervention(db, student_id, payload)
    except (StudentNotFoundError, FlagNotForStudentError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_service.record(
        db, user.id, "create", "intervention",
        resource_id=intervention.id, student_id=student_id,
    )
    return intervention


@router.get("/students/{student_id}/interventions", response_model=list[InterventionRead])
def list_interventions(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor", "administrator")),
) -> list[InterventionRead]:
    """List a student's interventions. Advisors and administrators can read."""
    try:
        rows = intervention_service.list_interventions(db, student_id)
    except StudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_service.record(db, user.id, "view", "interventions", student_id=student_id)
    return rows


@router.post("/interventions/{intervention_id}/outcome", response_model=InterventionRead)
def record_outcome(
    intervention_id: int,
    payload: OutcomeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor")),
) -> InterventionRead:
    """Record the advisor's outcome for an intervention. Advisors only."""
    try:
        intervention = intervention_service.record_outcome(db, intervention_id, payload)
    except InterventionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_service.record(
        db, user.id, "outcome", "intervention",
        resource_id=intervention_id, student_id=intervention.student_id,
    )
    return intervention


@router.get("/interventions/{intervention_id}/follow-up", response_model=FollowUpRead)
def get_follow_up(
    intervention_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor", "administrator")),
) -> FollowUpRead:
    """Compare indicators at the intervention date with the follow-up date."""
    try:
        result = intervention_service.get_follow_up(db, intervention_id)
    except InterventionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    intervention = result.intervention
    audit_service.record(
        db, user.id, "view", "follow_up",
        resource_id=intervention_id, student_id=intervention.student_id,
    )
    return FollowUpRead(
        intervention_id=intervention.id,
        student_id=intervention.student_id,
        intervention_date=intervention.intervention_date,
        follow_up_due=intervention.follow_up_due,
        is_due=result.is_due,
        outcome=intervention.outcome,
        before=IndicatorsRead.model_validate(result.before),
        after=IndicatorsRead.model_validate(result.after),
    )