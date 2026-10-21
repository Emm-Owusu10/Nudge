from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.indicator import IndicatorsRead

InterventionType = Literal["meeting", "study_plan", "tutoring_referral", "wellbeing_referral", "other"]

# The stored outcome can start as "not_yet_reviewed", but an advisor can only
# record one of the three real outcomes.
Outcome = Literal["improving", "no_change", "referred_elsewhere", "not_yet_reviewed"]
RecordableOutcome = Literal["improving", "no_change", "referred_elsewhere"]


class InterventionCreate(BaseModel):
    """The data an advisor sends to record an intervention. The student comes from the URL."""

    model_config = ConfigDict(extra="forbid")

    intervention_type: InterventionType
    intervention_date: date
    # max_length stops very long notes, and None means no notes were recorded.
    notes: str | None = Field(default=None, max_length=2000)
    flag_id: int | None = None


class InterventionRead(BaseModel):
    """The data returned for an intervention."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    flag_id: int | None
    intervention_type: InterventionType
    intervention_date: date
    follow_up_due: date
    notes: str | None
    outcome: Outcome
    outcome_recorded_at: datetime | None
    created_at: datetime


class OutcomeUpdate(BaseModel):
    """The outcome an advisor records after reviewing the follow-up."""

    model_config = ConfigDict(extra="forbid")

    outcome: RecordableOutcome


class FollowUpRead(BaseModel):
    """Indicators at the intervention date compared with indicators at the follow-up date."""

    intervention_id: int
    student_id: int
    intervention_date: date
    follow_up_due: date
    # False means the follow-up date hasn't arrived yet, so the "after" values are incomplete.
    is_due: bool
    outcome: Outcome
    before: IndicatorsRead
    after: IndicatorsRead