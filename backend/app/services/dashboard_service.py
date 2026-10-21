from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.flag import Flag
from app.models.lecturer_course import LecturerCourse
from app.models.student import Student

# Lower number means more urgent. Used to order the queue.
LEVEL_RANK = {"priority review": 0, "review recommended": 1, "monitor": 2}


def list_flag_queue(db: Session, as_of: date, status: str) -> list[tuple[Flag, Student]]:
    """Return flags for one evaluation date and status, most urgent first, then by student number."""
    statement = (
        select(Flag, Student)
        .join(Student, Student.id == Flag.student_id)
        .where(Flag.as_of == as_of, Flag.status == status)
    )
    rows = list(db.execute(statement).all())
    rows.sort(key=lambda row: (LEVEL_RANK.get(row[0].level, 9), row[1].student_number))
    return rows


def list_lecturer_courses(db: Session, user_id: int) -> list[Course]:
    """Return only the courses this lecturer is linked to, ordered by code."""
    statement = (
        select(Course)
        .join(LecturerCourse, LecturerCourse.course_id == Course.id)
        .where(LecturerCourse.user_id == user_id)
        .order_by(Course.code)
    )
    return list(db.scalars(statement))