from datetime import date

from pydantic import BaseModel, ConfigDict


class AttendanceWindowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rate: float | None
    sessions_counted: int


class MissingWorkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    missing: int
    considered: int


class GradeTrendRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recent_average: float | None
    earlier_average: float | None


class IndicatorsRead(BaseModel):
    """The full indicator response for one student."""

    model_config = ConfigDict(from_attributes=True)

    student_id: int
    as_of: date
    attendance_recent: AttendanceWindowRead
    attendance_earlier: AttendanceWindowRead
    missing_assignments: MissingWorkRead
    grades: GradeTrendRead