from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.assessment import AssessmentTitle
from app.schemas.attendance import AttendanceStatus
from app.schemas.course import CourseTitle
from app.schemas.student import PersonName, Programme


def _check_update_fields(model: BaseModel) -> BaseModel:
    """Shared rules for PATCH bodies: at least one field, and no explicit nulls."""
    if not model.model_fields_set:
        raise ValueError("Send at least one field to update")
    for name in model.model_fields_set:
        if getattr(model, name) is None:
            raise ValueError(f"'{name}' cannot be set to null")
    return model


class StudentUpdate(BaseModel):
    """Editable student fields. student_number is deliberately not editable."""

    model_config = ConfigDict(extra="forbid")

    full_name: PersonName | None = None
    programme: Programme | None = None

    @model_validator(mode="after")
    def check_fields(self):
        return _check_update_fields(self)


class CourseUpdate(BaseModel):
    """Editable course fields. The course code is deliberately not editable."""

    model_config = ConfigDict(extra="forbid")

    title: CourseTitle | None = None

    @model_validator(mode="after")
    def check_fields(self):
        return _check_update_fields(self)


class AttendanceUpdate(BaseModel):
    """Only the status can change. Student, course and date identify the record."""

    model_config = ConfigDict(extra="forbid")

    status: AttendanceStatus | None = None

    @model_validator(mode="after")
    def check_fields(self):
        return _check_update_fields(self)


class AssessmentUpdate(BaseModel):
    """Editable assessment fields. The student and course are fixed."""

    model_config = ConfigDict(extra="forbid")

    title: AssessmentTitle | None = None
    assessed_on: date | None = None
    score: Annotated[int, Field(ge=0, le=100)] | None = None

    @model_validator(mode="after")
    def check_fields(self):
        return _check_update_fields(self)