from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# Terms such as "2026-S1": digits, a hyphen, then a letter and digit.
AcademicTerm = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=20,
        pattern=r"^[0-9]{4}-[A-Z][0-9]$",
    ),
]


class EnrolmentCreate(BaseModel):
    """The data a client sends to enrol a student. The student comes from the URL."""

    model_config = ConfigDict(extra="forbid")

    course_id: int
    academic_term: AcademicTerm


class EnrolmentRead(BaseModel):
    """The data returned for an enrolment."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    academic_term: str