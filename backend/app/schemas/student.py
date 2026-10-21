from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# Student numbers: letters, digits and hyphens only. The pattern is checked
# after surrounding spaces are removed.
StudentNumber = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=20,
        pattern=r"^[A-Za-z0-9-]+$",
    ),
]

# Names can contain accents, apostrophes and hyphens, so we limit length only.
PersonName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Programme = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class StudentCreate(BaseModel):
    """The data a client must send to create a student."""

    # extra="forbid" rejects any field we didn't declare, such as "id" or
    # "created_at", instead of silently ignoring it.
    model_config = ConfigDict(extra="forbid")

    student_number: StudentNumber
    full_name: PersonName
    programme: Programme


class StudentRead(BaseModel):
    """The data the API returns for a student. It includes database-generated fields."""

    # from_attributes lets Pydantic read values from a SQLAlchemy object
    # as well as from a dictionary.
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_number: str
    full_name: str
    programme: str
    created_at: datetime