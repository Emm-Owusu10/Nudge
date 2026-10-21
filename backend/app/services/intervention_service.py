from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.flag import Flag
from app.models.intervention import Intervention
from app.models.student import Student
from app.schemas.intervention import InterventionCreate, OutcomeUpdate
from app.services.indicators import Indicators, StudentNotFoundError, calculate_indicators

# How long after an intervention the follow-up is compared.
FOLLOW_UP_DAYS = 42  # six weeks


class InterventionNotFoundError(Exception):
    """Raised when the intervention doesn't exist."""


class FlagNotForStudentError(Exception):
    """Raised when the flag doesn't exist or belongs to a different student."""


@dataclass(frozen=True)
class FollowUpResult:
    """The data needed to compare one intervention before and after."""

    intervention: Intervention
    is_due: bool
    before: Indicators
    after: Indicators


def _get_intervention(db: Session, intervention_id: int) -> Intervention:
    intervention = db.get(Intervention, intervention_id)
    if intervention is None:
        raise InterventionNotFoundError("Intervention not found")
    return intervention


def create_intervention(db: Session, student_id: int, data: InterventionCreate) -> Intervention:
    """Record an intervention and calculate its follow-up due date."""
    if db.get(Student, student_id) is None:
        raise StudentNotFoundError("Student not found")

    # A flag can only be linked if it belongs to this student. Otherwise an
    # advisor could attach one student's flag to another student's record.
    if data.flag_id is not None:
        flag = db.get(Flag, data.flag_id)
        if flag is None or flag.student_id != student_id:
            raise FlagNotForStudentError("Flag not found for this student")

    intervention = Intervention(
        student_id=student_id,
        flag_id=data.flag_id,
        intervention_type=data.intervention_type,
        intervention_date=data.intervention_date,
        follow_up_due=data.intervention_date + timedelta(days=FOLLOW_UP_DAYS),
        notes=data.notes,
        outcome="not_yet_reviewed",
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    return intervention


def list_interventions(db: Session, student_id: int) -> list[Intervention]:
    """Return a student's interventions, most recent first."""
    if db.get(Student, student_id) is None:
        raise StudentNotFoundError("Student not found")
    statement = (
        select(Intervention)
        .where(Intervention.student_id == student_id)
        .order_by(Intervention.intervention_date.desc(), Intervention.id.desc())
    )
    return list(db.scalars(statement))


def record_outcome(db: Session, intervention_id: int, data: OutcomeUpdate) -> Intervention:
    """Store the advisor's outcome and when it was recorded."""
    intervention = _get_intervention(db, intervention_id)
    intervention.outcome = data.outcome
    intervention.outcome_recorded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(intervention)
    return intervention


def get_follow_up(db: Session, intervention_id: int) -> FollowUpResult:
    """Compare indicators on the intervention date with indicators on the follow-up date."""
    intervention = _get_intervention(db, intervention_id)
    before = calculate_indicators(db, intervention.student_id, intervention.intervention_date)
    after = calculate_indicators(db, intervention.student_id, intervention.follow_up_due)
    return FollowUpResult(
        intervention=intervention,
        is_due=date.today() >= intervention.follow_up_due,
        before=before,
        after=after,
    )