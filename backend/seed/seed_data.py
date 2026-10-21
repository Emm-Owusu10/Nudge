"""Create synthetic demonstration data in the development database.

Run once, from the backend folder:
    python -m seed.seed_data

The script uses the application's service functions, so validation and the
flag rules apply to the seeded data. It bypasses the HTTP layer and does not
write audit entries, because it is a setup tool, not a user action.
"""

import getpass
import sys
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.lecturer_course import LecturerCourse
from app.models.course import Course
from app.models.student import Student
from app.models.user import User
from app.schemas.assessment import AssessmentCreate
from app.schemas.assignment import AssignmentCreate
from app.schemas.attendance import AttendanceCreate
from app.schemas.course import CourseCreate
from app.schemas.enrolment import EnrolmentCreate
from app.schemas.student import StudentCreate
from app.schemas.submission import SubmissionUpdate
from app.services import (
    assessment_service,
    assignment_service,
    attendance_service,
    course_service,
    enrolment_service,
    flag_service,
    student_service,
)

TERM = "2026-S1"
AS_OF = date(2026, 10, 19)
RECENT_WINDOW_START = date(2026, 9, 21)  # matches the indicator window boundary
COURSE_CODE = "SEED-CS101"
DEMO_STUDENT_PREFIX = "DEMO-"
DEMO_USERNAMES = ("advisor.demo", "lecturer.demo")
MIN_PASSWORD_LENGTH = 12

GROUP_SIZES = {"steady": 5, "declining": 4, "struggling": 3}

ASSESSMENTS = {
    "steady": [
        ("Quiz 1", date(2026, 8, 10), 71),
        ("Quiz 2", date(2026, 8, 24), 74),
        ("Midterm", date(2026, 9, 7), 72),
        ("Quiz 3", date(2026, 9, 21), 75),
        ("Quiz 4", date(2026, 10, 5), 73),
        ("Final coursework", date(2026, 10, 12), 74),
    ],
    "declining": [
        ("Quiz 1", date(2026, 8, 10), 76),
        ("Quiz 2", date(2026, 8, 24), 74),
        ("Midterm", date(2026, 9, 7), 75),
        ("Quiz 3", date(2026, 9, 21), 62),
        ("Quiz 4", date(2026, 10, 5), 58),
        ("Final coursework", date(2026, 10, 12), 55),
    ],
    "struggling": [
        ("Quiz 1", date(2026, 8, 10), 48),
        ("Quiz 2", date(2026, 8, 24), 52),
        ("Midterm", date(2026, 9, 7), 50),
        ("Quiz 3", date(2026, 9, 21), 47),
        ("Quiz 4", date(2026, 10, 5), 51),
        ("Final coursework", date(2026, 10, 12), 49),
    ],
}

ASSIGNMENT_DUE_DATES = [
    date(2026, 9, 4),
    date(2026, 9, 18),
    date(2026, 10, 2),
    date(2026, 10, 9),
    date(2026, 10, 16),
]


def session_dates() -> list[date]:
    """Monday and Thursday sessions from early August up to the evaluation date."""
    day = date(2026, 8, 3)
    sessions = []
    while day <= AS_OF:
        if day.weekday() in (0, 3):  # Monday and Thursday
            sessions.append(day)
        day += timedelta(days=1)
    return sessions


def attendance_status(profile: str, index: int, recent: bool) -> str:
    """Deterministic attendance pattern for each group."""
    if profile == "steady":
        if index == 3:
            return "excused"
        return "absent" if index % 7 == 0 else "present"
    if profile == "declining":
        if recent:
            return "present" if index % 4 == 0 else "absent"
        return "absent" if index % 7 == 0 else "present"
    # struggling
    return "present" if index % 3 == 0 else "absent"


def check_database() -> None:
    """Stop unless the connection points at the development database."""
    name = make_url(get_settings().database_url).database
    if name != "early_intervention" or name.endswith("_test"):
        sys.exit(f"Refusing to seed database '{name}'. Seeding runs only on 'early_intervention'.")


def check_not_already_seeded(db) -> None:
    """Stop if demo records already exist, so the script cannot run twice."""
    student_exists = db.scalar(
        select(Student.id).where(Student.student_number.like(f"{DEMO_STUDENT_PREFIX}%")).limit(1)
    )
    course_exists = db.scalar(select(Course.id).where(Course.code == COURSE_CODE).limit(1))
    user_exists = db.scalar(select(User.id).where(User.username.in_(DEMO_USERNAMES)).limit(1))
    if student_exists or course_exists or user_exists:
        sys.exit(
            "Demo data already exists in this database. The seed script runs once. "
            "Rebuild the development database to start again."
        )


def prompt_password() -> str:
    """Ask for the demo account password twice, without echoing it."""
    password = getpass.getpass("Password for the demo accounts: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if getpass.getpass("Repeat password: ") != password:
        sys.exit("Passwords do not match.")
    return password


def create_demo_users(db, password: str) -> User:
    """Create the demo advisor and lecturer. Returns the lecturer."""
    advisor = User(
        username="advisor.demo", password_hash=hash_password(password), role="advisor"
    )
    lecturer = User(
        username="lecturer.demo", password_hash=hash_password(password), role="lecturer"
    )
    db.add_all([advisor, lecturer])
    db.commit()
    db.refresh(lecturer)
    return lecturer


def main() -> None:
    check_database()
    password = prompt_password()

    print("This will write synthetic demonstration data to the 'early_intervention' database.")
    if input("Type SEED to continue: ").strip() != "SEED":
        sys.exit("Cancelled. Nothing was written.")

    with SessionLocal() as db:
        check_not_already_seeded(db)

        # 1. Users and the course, with the lecturer linked to it.
        lecturer = create_demo_users(db, password)
        course = course_service.create_course(
            db, CourseCreate(code=COURSE_CODE, title="Introduction to Programming (demo)")
        )
        db.add(LecturerCourse(user_id=lecturer.id, course_id=course.id))
        db.commit()

        # 2. Students and enrolments. These must exist before assignments are created,
        #    because each assignment gets a submission row for every enrolled student.
        students = []  # (student_id, group)
        number = 1
        for group, size in GROUP_SIZES.items():
            for _ in range(size):
                student = student_service.create_student(
                    db,
                    StudentCreate(
                        student_number=f"{DEMO_STUDENT_PREFIX}{number:03d}",
                        full_name=f"Demo Student {number:02d}",
                        programme="Demo Programme",
                    ),
                )
                enrolment_service.create_enrolment(
                    db, student.id, EnrolmentCreate(course_id=course.id, academic_term=TERM)
                )
                students.append((student.id, group))
                number += 1

        # 3. Assignments. Creating each one also creates a 'missing' row per student.
        assignments = []
        for index, due in enumerate(ASSIGNMENT_DUE_DATES, start=1):
            assignments.append(
                assignment_service.create_assignment(
                    db,
                    AssignmentCreate(
                        course_id=course.id,
                        academic_term=TERM,
                        title=f"Assignment {index}",
                        due_date=due,
                    ),
                )
            )

        # 4. Attendance, assessments and submissions, per student.
        sessions = session_dates()
        for student_id, group in students:
            for index, day in enumerate(sessions):
                attendance_service.record_attendance(
                    db,
                    student_id,
                    AttendanceCreate(
                        course_id=course.id,
                        session_date=day,
                        status=attendance_status(group, index, day > RECENT_WINDOW_START),
                    ),
                )

            for title, day, score in ASSESSMENTS[group]:
                assessment_service.record_assessment(
                    db,
                    student_id,
                    AssessmentCreate(
                        course_id=course.id, title=title, assessed_on=day, score=score
                    ),
                )

            for assignment_number, assignment in enumerate(assignments):
                # Struggling students leave the first three assignments unsubmitted.
                if group == "struggling" and assignment_number < 3:
                    continue
                rows = assignment_service.list_submissions(db, assignment.id)
                row = next(r for r in rows if r.student_id == student_id)
                assignment_service.update_submission(
                    db,
                    row.id,
                    SubmissionUpdate(
                        status="submitted",
                        submitted_on=assignment.due_date - timedelta(days=1),
                    ),
                )

        # 5. Evaluate every student as of the demo date, and print the results.
        print()
        print(f"Seeded {len(students)} students. Flags as of {AS_OF.isoformat()}:")
        group_by_id = dict(students)
        for student_id, group in students:
            flag = flag_service.evaluate_student(db, student_id, AS_OF)
            student = db.get(Student, student_id)
            if flag is None:
                print(f"  {student.student_number}  {group:<11} no flag")
            else:
                messages = "; ".join(factor["message"] for factor in flag.factors)
                print(f"  {student.student_number}  {group:<11} {flag.level}: {messages}")

        print()
        print("Demo accounts created (use the password you entered):")
        print("  advisor.demo    (advisor)")
        print("  lecturer.demo   (lecturer, teaches SEED-CS101)")


if __name__ == "__main__":
    main()