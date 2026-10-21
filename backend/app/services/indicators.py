from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.student import Student
from app.models.submission import Submission

# Window and sample sizes. Changing them changes every indicator, so they are
# kept in one place and documented in docs/05-indicators.md.
ATTENDANCE_WINDOW_DAYS = 28
ASSIGNMENT_WINDOW_SIZE = 5
GRADE_GROUP_SIZE = 3


class StudentNotFoundError(Exception):
    """Raised when the student doesn't exist."""


@dataclass(frozen=True)
class WindowRate:
    """Attendance rate for one time window. rate is None when no sessions were counted."""

    rate: float | None
    sessions_counted: int


@dataclass(frozen=True)
class MissingWork:
    """How many of the most recent assignments are still missing."""

    missing: int
    considered: int


@dataclass(frozen=True)
class GradeTrend:
    """Average of the most recent group of scores, and of the group before it."""

    recent_average: float | None
    earlier_average: float | None


@dataclass(frozen=True)
class Indicators:
    """All indicators for one student on one date."""

    student_id: int
    as_of: date
    attendance_recent: WindowRate
    attendance_earlier: WindowRate
    missing_assignments: MissingWork
    grades: GradeTrend


def _attendance_rate(records: list[Attendance]) -> WindowRate:
    """Share of counted sessions that were present or late. Excused sessions are ignored."""
    counted = [record for record in records if record.status != "excused"]
    if not counted:
        return WindowRate(rate=None, sessions_counted=0)
    attended = sum(1 for record in counted if record.status in ("present", "late"))
    return WindowRate(rate=attended / len(counted), sessions_counted=len(counted))


def _average(scores: list[int], group_size: int) -> float | None:
    """Mean of a full group of scores. Returns None if the group is incomplete."""
    if len(scores) < group_size:
        return None
    return sum(scores) / len(scores)


def calculate_indicators(db: Session, student_id: int, as_of: date) -> Indicators:
    """Work out every indicator for one student as they stood on as_of."""
    if db.get(Student, student_id) is None:
        raise StudentNotFoundError("Student not found")

    # Attendance: load one combined window, then split it into recent and earlier.
    recent_start = as_of - timedelta(days=ATTENDANCE_WINDOW_DAYS)
    earlier_start = as_of - timedelta(days=2 * ATTENDANCE_WINDOW_DAYS)
    attendance_rows = db.scalars(
        select(Attendance).where(
            Attendance.student_id == student_id,
            Attendance.session_date > earlier_start,
            Attendance.session_date <= as_of,
        )
    ).all()
    recent_rows = [row for row in attendance_rows if row.session_date > recent_start]
    earlier_rows = [row for row in attendance_rows if row.session_date <= recent_start]

    # Missing work: the most recent assignments due by as_of, newest first.
    submission_statuses = list(
        db.scalars(
            select(Submission.status)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .where(Submission.student_id == student_id, Assignment.due_date <= as_of)
            .order_by(Assignment.due_date.desc(), Assignment.id.desc())
            .limit(ASSIGNMENT_WINDOW_SIZE)
        )
    )

    # Grades: the newest scores by as_of, split into two groups.
    scores = list(
        db.scalars(
            select(Assessment.score)
            .where(Assessment.student_id == student_id, Assessment.assessed_on <= as_of)
            .order_by(Assessment.assessed_on.desc(), Assessment.id.desc())
        )
    )
    recent_scores = scores[:GRADE_GROUP_SIZE]
    earlier_scores = scores[GRADE_GROUP_SIZE : 2 * GRADE_GROUP_SIZE]

    return Indicators(
        student_id=student_id,
        as_of=as_of,
        attendance_recent=_attendance_rate(recent_rows),
        attendance_earlier=_attendance_rate(earlier_rows),
        missing_assignments=MissingWork(
            missing=submission_statuses.count("missing"),
            considered=len(submission_statuses),
        ),
        grades=GradeTrend(
            recent_average=_average(recent_scores, GRADE_GROUP_SIZE),
            earlier_average=_average(earlier_scores, GRADE_GROUP_SIZE),
        ),
    )