from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.access_service import (
    AccessDeniedError,
    ensure_course_access,
    ensure_student_access,
)

# auto_error=False lets us return our own 401 response, with the same shape every time.
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorised(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Return the logged-in user, or raise 401 if the request has no valid token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorised("Not authenticated")

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise _unauthorised("Invalid or expired token")

    # Load the user on every request, so deactivation and role changes apply immediately.
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorised("Invalid or expired token")
    return user


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    """Allow only the listed roles. Returns 403 for any other logged-in user."""

    def check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to do this",
            )
        return user

    return check_role


def student_scope(
    student_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Allow access to a student's records only if the user is in scope. Otherwise return 404."""
    try:
        ensure_student_access(db, user, student_id)
    except AccessDeniedError as exc:
        # Same response as a missing student, so student numbers can't be probed.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found") from exc
    return user


def check_course_scope(
    db: Session,
    user: User,
    course_id: int,
    not_found_detail: str = "Course not found",
) -> None:
    """Call inside a handler when the course comes from the request or the record being changed."""
    try:
        ensure_course_access(db, user, course_id)
    except AccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail) from exc