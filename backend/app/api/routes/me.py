from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.course import CourseRead
from app.services import dashboard_service

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/courses", response_model=list[CourseRead])
def my_courses(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("lecturer")),
) -> list[CourseRead]:
    """The courses the logged-in lecturer teaches. Lecturers only."""
    return dashboard_service.list_lecturer_courses(db, user.id)