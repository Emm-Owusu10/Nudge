from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Intervention(Base):
    """A support action an advisor took for one student. Maps to 'interventions'."""

    __tablename__ = "interventions"
    __table_args__ = (
        CheckConstraint(
            "intervention_type IN ('meeting', 'study_plan', 'tutoring_referral', "
            "'wellbeing_referral', 'other')",
            name="ck_intervention_type",
        ),
        CheckConstraint(
            "outcome IN ('improving', 'no_change', 'referred_elsewhere', 'not_yet_reviewed')",
            name="ck_intervention_outcome",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    # Optional link to the flag that prompted this intervention. Empty if the
    # advisor acted without a flag.
    flag_id: Mapped[int | None] = mapped_column(ForeignKey("flags.id"), nullable=True)
    intervention_type: Mapped[str] = mapped_column(String(30))
    intervention_date: Mapped[date] = mapped_column(Date)
    # Stored rather than calculated, so the due date never changes if the
    # follow-up window setting is changed later.
    follow_up_due: Mapped[date] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(String(30), server_default="not_yet_reviewed")
    outcome_recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )