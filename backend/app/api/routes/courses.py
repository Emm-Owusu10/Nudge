from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import check_course_scope, get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.course import CourseCreate, CourseRead
from app.schemas.student import StudentRead
from app.schemas.updates import CourseUpdate
from app.services import audit_service, course_service
from app.services.course_service import CourseNotFoundError, DuplicateCourseCodeError

router = APIRouter(prefix="/courses", tags=["courses"])

ACADEMIC_TERM_PATTERN = r"^[0-9]{4}-[A-Z][0-9]$"


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("administrator")),
) -> CourseRead:
    """Create a course. Administrators only."""
    try:
        course = course_service.create_course(db, payload)
    except DuplicateCourseCodeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    audit_service.record(db, user.id, "create", "course", resource_id=course.id)
    return course


@router.get("", response_model=list[CourseRead])
def list_courses(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[CourseRead]:
    """List courses. Any logged-in user can read course details."""
    return course_service.list_courses(db, limit=limit, offset=offset)


@router.get("/{course_id}", response_model=CourseRead)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> CourseRead:
    """Return one course, or 404 if it doesn't exist."""
    course = course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.patch("/{course_id}", response_model=CourseRead)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("administrator")),
) -> CourseRead:
    """Correct a course title. Administrators only."""
    try:
        course = course_service.update_course(db, course_id, payload)
    except CourseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_service.record(db, user.id, "update", "course", resource_id=course_id)
    return course


@router.get("/{course_id}/students", response_model=list[StudentRead])
def list_course_students(
    course_id: int,
    academic_term: str | None = Query(default=None, pattern=ACADEMIC_TERM_PATTERN),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("lecturer", "advisor", "administrator")),
) -> list[StudentRead]:
    """The roster for a course. Lecturers can open only courses they teach."""
    check_course_scope(db, user, course_id)
    try:
        students = course_service.list_course_students(db, course_id, academic_term)
    except CourseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    audit_service.record(db, user.id, "view", "course_roster", resource_id=course_id)
    return students