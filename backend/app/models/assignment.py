from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Assignment(Base):
    """A piece of assessed work in one course for one term. Maps to 'assignments'."""

    __tablename__ = "assignments"
    __table_args__ = (
        # The same title can't be used twice for one course in one term.
        UniqueConstraint(
            "course_id", "academic_term", "title",
            name="uq_assignment_course_term_title",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    academic_term: Mapped[str] = mapped_column(String(20))  # must match enrolments
    title: Mapped[str] = mapped_column(String(120))
    due_date: Mapped[date] = mapped_column(Date)