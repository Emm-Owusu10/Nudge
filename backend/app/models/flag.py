from datetime import date, datetime

from sqlalchemy import JSON, CheckConstraint, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Flag(Base):
    """A review flag raised for one student on one date. Maps to 'flags'."""

    __tablename__ = "flags"
    __table_args__ = (
        # One flag per student per evaluation date. Re-running the evaluation
        # for the same date returns the existing flag instead of adding another.
        UniqueConstraint("student_id", "as_of", name="uq_flag_student_as_of"),
        CheckConstraint(
            "level IN ('monitor', 'review recommended', 'priority review')",
            name="ck_flag_level",
        ),
        CheckConstraint("status IN ('open', 'dismissed')", name="ck_flag_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    as_of: Mapped[date] = mapped_column(Date)
    level: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(10))
    # Each entry is {"code": "...", "message": "..."}. Stored as JSON so the
    # reasons are kept exactly as they were when the flag was raised.
    factors: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    dismissal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)