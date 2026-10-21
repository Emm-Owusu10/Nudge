from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """One record of who viewed or changed what, and when. Maps to 'audit_logs'."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            "action IN ('create', 'update', 'view', 'evaluate', 'dismiss', 'outcome')",
            name="ck_audit_action",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(20))
    # The kind of record touched, such as "student", "attendance" or "flag".
    resource: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # The student whose data was touched. Filled for every student-related action,
    # so the log can answer "who looked at this student's record?"
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )