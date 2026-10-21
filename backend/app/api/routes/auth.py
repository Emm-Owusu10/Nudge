from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.auth import CurrentUserRead, LoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Exchange a username and password for a bearer token."""
    user = auth_service.authenticate_user(db, payload.username, payload.password)
    if user is None:
        # The same message for every failure, so the response doesn't reveal which part was wrong.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_in = create_access_token(user.id)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=CurrentUserRead)
def read_current_user(user: User = Depends(get_current_user)) -> User:
    """Return the user the token belongs to. Useful for checking a login works."""
    return user