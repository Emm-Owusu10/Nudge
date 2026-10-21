from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Assessment(Base):
    """A scored assessment for one student in one course. Maps to 'assessments'."""

    __tablename__ = "assessments"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_assessment_score_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(120))  # e.g. "Midterm" or "Essay 1"
    assessed_on: Mapped[date] = mapped_column(Date)
    score: Mapped[int] = mapped_column(Integer)  # percentage, 0 to 100