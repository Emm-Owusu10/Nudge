from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

SubmissionStatus = Literal["submitted", "missing", "late"]


class SubmissionUpdate(BaseModel):
    """The data a lecturer sends to update one submission."""

    model_config = ConfigDict(extra="forbid")

    status: SubmissionStatus
    submitted_on: date | None = None

    @model_validator(mode="after")
    def check_date_matches_status(self):
        """Stop contradictions such as 'missing' with a submission date."""
        if self.status == "missing" and self.submitted_on is not None:
            raise ValueError("submitted_on must be empty when status is 'missing'")
        if self.status in ("submitted", "late") and self.submitted_on is None:
            raise ValueError("submitted_on is required when status is 'submitted' or 'late'")
        return self


class SubmissionRead(BaseModel):
    """The data returned for one submission."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    student_id: int
    status: SubmissionStatus
    submitted_on: date | None