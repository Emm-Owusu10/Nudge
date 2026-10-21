from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["advisor", "lecturer", "administrator"]


class LoginRequest(BaseModel):
    """Credentials sent to the login endpoint."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50)
    # The maximum length stops someone sending a huge password to slow down the server.
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    """The token returned after a successful login."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class CurrentUserRead(BaseModel):
    """The logged-in user. The password hash is never included."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: Role