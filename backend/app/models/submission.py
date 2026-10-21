from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Submission(Base):
    """One student's submission status for one assignment. Maps to 'submissions'."""

    __tablename__ = "submissions"
    __table_args__ = (
        # Exactly one submission row per student per assignment.
        UniqueConstraint("assignment_id", "student_id", name="uq_submission_assignment_student"),
        CheckConstraint("status IN ('submitted', 'missing', 'late')", name="ck_submission_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    status: Mapped[str] = mapped_column(String(10))
    # Empty when the work is missing. Filled in when it's submitted or late.
    submitted_on: Mapped[date | None] = mapped_column(Date, nullable=True)