from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Student(Base):
    """A student whose academic records are tracked. Maps to the 'students' table."""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_number: Mapped[str] = mapped_column(String(20), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    programme: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Not a database column. It lets Python code walk from a student to
    # their enrolments. The real link is the foreign key on the enrolments table.
    enrolments: Mapped[list["Enrolment"]] = relationship(back_populates="student")