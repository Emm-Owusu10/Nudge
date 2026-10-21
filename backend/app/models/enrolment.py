from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Enrolment(Base):
    """A student taking a course in a given term. Maps to the 'enrolments' table."""

    __tablename__ = "enrolments"

    # A student can take the same course once per term, so the combination
    # must be unique. The database enforces this rule.
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", "academic_term",
            name="uq_enrolment_student_course_term",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # ForeignKey stores a student's id here and makes PostgreSQL check that
    # the student actually exists. We don't use ondelete="CASCADE", so deleting
    # a student is refused while they still have enrolments. Academic records
    # should be kept, not silently removed.
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    academic_term: Mapped[str] = mapped_column(String(20))  # e.g. "2026-S1"

    student: Mapped["Student"] = relationship(back_populates="enrolments")
    course: Mapped["Course"] = relationship(back_populates="enrolments")