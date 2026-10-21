from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# pool_pre_ping checks that a pooled connection is still alive before using it.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# expire_on_commit=False keeps loaded values readable after a commit. Audit entries
# commit during a request, and this stops responses from reloading rows afterwards.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield one database session per request, and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()