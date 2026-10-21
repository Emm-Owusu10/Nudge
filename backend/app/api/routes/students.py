from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles, student_scope
from app.db.session import get_db
from app.models.user import User
from app.schemas.student import StudentCreate, StudentRead
from app.schemas.updates import StudentUpdate
from app.services import audit_service, student_service
from app.services.student_service import DuplicateStudentNumberError, StudentNotFoundError

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("administrator")),
) -> StudentRead:
    """Create a student. Administrators only."""
    try:
        student = student_service.create_student(db, payload)
    except DuplicateStudentNumberError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    audit_service.record(db, user.id, "create", "student", resource_id=student.id, student_id=student.id)
    return student


@router.get("", response_model=list[StudentRead])
def list_students(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor", "administrator")),
) -> list[StudentRead]:
    """List students. Advisors and administrators only, because lecturers see their own rosters."""
    students = student_service.list_students(db, limit=limit, offset=offset)
    audit_service.record(db, user.id, "view", "student_list")
    return students


@router.get(
    "/{student_id}",
    response_model=StudentRead,
    dependencies=[Depends(student_scope)],
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("advisor", "administrator", "lecturer")),
) -> StudentRead:
    """Return one student. Lecturers can see only students in their courses."""
    student = student_service.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    audit_service.record(db, user.id, "view", "student", resource_id=student_id, student_id=student_id)
    return student


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("administrator")),
) -> StudentRead:
    """Correct a student's name or programme. Administrators only."""
    try:
        student = student_service.update_student(db, student_id, payload)
    except StudentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_service.record(db, user.id, "update", "student", resource_id=student_id, student_id=student_id)
    return student