from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

AssessmentTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class AssessmentCreate(BaseModel):
    """The data a client sends to record a score. The student comes from the URL."""

    model_config = ConfigDict(extra="forbid")

    course_id: int
    title: AssessmentTitle
    assessed_on: date
    # ge and le reject scores outside 0 to 100 before they reach the database.
    score: int = Field(ge=0, le=100)


class AssessmentRead(BaseModel):
    """The data returned for one assessment score."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    title: str
    assessed_on: date
    score: int