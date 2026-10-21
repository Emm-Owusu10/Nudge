from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles, student_scope
from app.db.session import get_db
from app.models.user import User
from app.schemas.enrolment import EnrolmentCreate, EnrolmentRead
from app.services import audit_service, enrolment_service
from app.services.enrolment_service import (
    CourseNotFoundError,
    DuplicateEnrolmentError,
    StudentNotFoundError,
)

router = APIRouter(prefix="/students/{student_id}/enrolments", tags=["enrolments"])


@router.post("", response_model=EnrolmentRead, status_code=status.HTTP_201_CREATED)
def create_enrolment(
    student_id: int,
    payload: EnrolmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("administrator")),
) -> EnrolmentRead:
    """Enrol a student in a course. Administrators only."""
    try:
        enrolment = enrolment_service.create_enrolment(db, student_id, payload)
    except (StudentNotFoundError, CourseNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateEnrolmentError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    audit_service.record(db, user.id, "create", "enrolment", resource_id=enrolment.id, student_id=student_id)
    return enrolment


@router.get("", response_model=list[EnrolmentRead], dependencies=[Depends(student_scope)])
def list_enrolments(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor", "administrator", "lecturer")),
) -> list[EnrolmentRead]:
    """List a student's enrolments, for users who can see that student."""
    rows = enrolment_service.list_enrolments(db, student_id)
    audit_service.record(db, user.id, "view", "enrolments", student_id=student_id)
    return rows