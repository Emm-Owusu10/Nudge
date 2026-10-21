from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User

# Used when a username doesn't exist. Checking a password against this hash
# takes about as long as a real check, so the response time doesn't reveal
# which usernames exist.
_DUMMY_HASH = hash_password("not-the-password-for-any-account")


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Return the user if the credentials are valid and the account is active, otherwise None."""
    normalised = username.strip().lower()
    user = db.scalar(select(User).where(User.username == normalised))

    if user is None:
        verify_password(_DUMMY_HASH, password)
        return None

    password_ok = verify_password(user.password_hash, password)
    if not password_ok or not user.is_active:
        return None
    return user