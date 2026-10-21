from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# Course codes such as "CS101" or "MATH-200": letters, digits and hyphens only.
CourseCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=20,
        pattern=r"^[A-Za-z0-9-]+$",
    ),
]

CourseTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class CourseCreate(BaseModel):
    """The data a client must send to create a course."""

    # Reject any field we didn't declare, such as "id".
    model_config = ConfigDict(extra="forbid")

    code: CourseCode
    title: CourseTitle


class CourseRead(BaseModel):
    """The data the API returns for a course."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str