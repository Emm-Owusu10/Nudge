from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

DismissalReason = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]


class FlagFactorRead(BaseModel):
    """One reason for a flag."""

    code: str
    message: str


class FlagRead(BaseModel):
    """The data returned for a flag."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    as_of: date
    level: str
    status: str
    factors: list[FlagFactorRead]
    created_at: datetime
    dismissal_reason: str | None
    dismissed_at: datetime | None


class FlagDismiss(BaseModel):
    """The data an advisor sends to dismiss a flag. A reason is required."""

    model_config = ConfigDict(extra="forbid")

    reason: DismissalReason