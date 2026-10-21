from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.flag import Flag
from app.models.student import Student
from app.services.indicators import StudentNotFoundError, calculate_indicators
from app.services.rules import evaluate_rules


class FlagNotFoundError(Exception):
    """Raised when the flag doesn't exist."""


class FlagAlreadyDismissedError(Exception):
    """Raised when someone tries to dismiss a flag that is already dismissed."""


def evaluate_student(db: Session, student_id: int, as_of: date) -> Flag | None:
    """Calculate indicators, apply the rules, and store a flag if one applies.

    Returns the existing flag if this date was already evaluated, or None when
    no rule fires.
    """
    indicators = calculate_indicators(db, student_id, as_of)  # raises if the student is missing
    level, factors = evaluate_rules(indicators)
    if level is None:
        return None

    existing = db.scalar(
        select(Flag).where(Flag.student_id == student_id, Flag.as_of == as_of)
    )
    if existing is not None:
        return existing

    flag = Flag(
        student_id=student_id,
        as_of=as_of,
        level=level,
        status="open",
        factors=[{"code": factor.code, "message": factor.message} for factor in factors],
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag


def list_flags(db: Session, student_id: int) -> list[Flag]:
    """Return a student's flags, newest evaluation date first."""
    if db.get(Student, student_id) is None:
        raise StudentNotFoundError("Student not found")
    statement = (
        select(Flag)
        .where(Flag.student_id == student_id)
        .order_by(Flag.as_of.desc(), Flag.id.desc())
    )
    return list(db.scalars(statement))


def dismiss_flag(db: Session, flag_id: int, reason: str) -> Flag:
    """Mark a flag as dismissed and record the advisor's reason."""
    flag = db.get(Flag, flag_id)
    if flag is None:
        raise FlagNotFoundError("Flag not found")
    if flag.status == "dismissed":
        raise FlagAlreadyDismissedError("Flag has already been dismissed")

    flag.status = "dismissed"
    flag.dismissal_reason = reason
    flag.dismissed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(flag)
    return flag