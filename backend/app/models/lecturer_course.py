from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LecturerCourse(Base):
    """Links a lecturer to a course they teach. Maps to 'lecturer_courses'."""

    __tablename__ = "lecturer_courses"
    __table_args__ = (
        # A lecturer is linked to a course only once.
        UniqueConstraint("user_id", "course_id", name="uq_lecturer_course"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))