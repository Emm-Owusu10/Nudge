from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.flag import FlagFactorRead


class FlagQueueItem(BaseModel):
    """One flag in the advisor queue, with enough student detail to act on it."""

    flag_id: int
    student_id: int
    student_number: str
    full_name: str
    level: str
    status: str
    as_of: date
    factors: list[FlagFactorRead]
    created_at: datetime