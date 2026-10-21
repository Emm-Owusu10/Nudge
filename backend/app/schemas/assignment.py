from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas.enrolment import AcademicTerm  # same term format as enrolments

AssignmentTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class AssignmentCreate(BaseModel):
    """The data a client sends to create an assignment."""

    model_config = ConfigDict(extra="forbid")

    course_id: int
    academic_term: AcademicTerm
    title: AssignmentTitle
    due_date: date


class AssignmentRead(BaseModel):
    """The data returned for an assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    academic_term: str
    title: str
    due_date: date