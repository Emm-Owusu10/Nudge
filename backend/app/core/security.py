from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

# One hasher is enough. It holds the Argon2 settings and creates salts itself.
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return an Argon2 hash. The result includes a random salt, so hashing the same password twice gives different output."""
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Return True only if the password matches the stored hash."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        # VerificationError covers a wrong password. InvalidHashError covers a corrupted stored hash.
        return False


def create_access_token(user_id: int) -> tuple[str, int]:
    """Create a signed token for a user. Returns the token and its lifetime in seconds."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    lifetime_seconds = settings.access_token_minutes * 60
    payload = {
        "sub": str(user_id),  # the subject: whose token this is
        "iat": now,           # issued at
        "exp": now + timedelta(seconds=lifetime_seconds),  # expiry, checked automatically on decode
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, lifetime_seconds


def decode_access_token(token: str) -> int | None:
    """Return the user id inside a valid token, or None if it's forged, expired or malformed."""
    settings = get_settings()
    try:
        # jwt.decode checks the signature and the expiry time.
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.InvalidTokenError:
        return None
    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        return None