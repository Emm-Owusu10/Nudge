from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Attendance(Base):
    """One attendance record: a student's status in one course on one date. Maps to 'attendance'."""

    __tablename__ = "attendance"
    __table_args__ = (
        # A student can have only one record per course per session date.
        UniqueConstraint(
            "student_id", "course_id", "session_date",
            name="uq_attendance_student_course_session",
        ),
        # The database rejects any status outside this list, even if code has a bug.
        CheckConstraint(
            "status IN ('present', 'absent', 'late', 'excused')",
            name="ck_attendance_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    session_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10))