from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

# Literal limits the value to exactly these four strings. Anything else,
# such as "sick", is rejected with a 422 error before the database is touched.
AttendanceStatus = Literal["present", "absent", "late", "excused"]


class AttendanceCreate(BaseModel):
    """The data a client sends to record attendance. The student comes from the URL."""

    model_config = ConfigDict(extra="forbid")

    course_id: int
    session_date: date
    status: AttendanceStatus


class AttendanceRead(BaseModel):
    """The data returned for one attendance record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    session_date: date
    status: AttendanceStatus