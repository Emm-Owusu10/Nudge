from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import check_course_scope, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentRead
from app.schemas.submission import SubmissionRead
from app.services import assignment_service, audit_service
from app.services.assignment_service import (
    AssignmentNotFoundError,
    CourseNotFoundError,
    DuplicateAssignmentError,
)

router = APIRouter(prefix="/assignments", tags=["assignments"])

READ_ROLES = ("lecturer", "advisor", "administrator")


@router.post("", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("lecturer")),
) -> AssignmentRead:
    """Create an assignment. Lecturers only, and only for their own courses."""
    check_course_scope(db, user, payload.course_id)
    try:
        assignment = assignment_service.create_assignment(db, payload)
    except CourseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    audit_service.record(db, user.id, "create", "assignment", resource_id=assignment.id)
    return assignment


@router.get("/{assignment_id}", response_model=AssignmentRead)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*READ_ROLES)),
) -> AssignmentRead:
    """Return one assignment. Lecturers see only assignments in their courses."""
    try:
        assignment = assignment_service.get_assignment(db, assignment_id)
    except AssignmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    check_course_scope(db, user, assignment.course_id, not_found_detail="Assignment not found")
    return assignment


@router.get("/{assignment_id}/submissions", response_model=list[SubmissionRead])
def list_submissions(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*READ_ROLES)),
) -> list[SubmissionRead]:
    """Return the submission status of every enrolled student for one assignment."""
    try:
        assignment = assignment_service.get_assignment(db, assignment_id)
        rows = assignment_service.list_submissions(db, assignment_id)
    except AssignmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    check_course_scope(db, user, assignment.course_id, not_found_detail="Assignment not found")
    audit_service.record(db, user.id, "view", "submissions", resource_id=assignment_id)
    return rows