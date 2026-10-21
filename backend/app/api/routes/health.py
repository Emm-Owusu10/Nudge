from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db

# A router is a group of related endpoints. main.py attaches it to the app.
router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """Return 200 if PostgreSQL answers a simple query, otherwise 503."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        # Chain the original error so it appears in the server log,
        # but return only a generic message to the client.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unreachable",
        ) from exc
    return {"status": "ok", "database": "connected"}