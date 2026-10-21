"""Administration commands for the early intervention backend.

Run from the backend folder, for example:
    python manage.py create-user --username admin --role administrator
    python manage.py assign-course --username lecturer1 --course-code CS101
"""

import argparse
import getpass
import re
import sys

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.course import Course
from app.models.lecturer_course import LecturerCourse
from app.models.user import User

ROLES = ("advisor", "lecturer", "administrator")
# Lowercase letters, digits, dot, underscore and hyphen, 3 to 50 characters.
USERNAME_PATTERN = re.compile(r"^[a-z0-9_.-]{3,50}$")
MIN_PASSWORD_LENGTH = 12


def create_user(username: str, role: str) -> int:
    """Create a user after prompting for a password twice. Returns the new user id."""
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 3 to 50 characters: lowercase letters, digits, '.', '_' or '-'")

    # getpass hides the typing and keeps the password out of the command history.
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Repeat password: ")
    if password != confirmation:
        raise ValueError("Passwords do not match")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    with SessionLocal() as db:
        user = User(username=username, password_hash=hash_password(password), role=role)
        db.add(user)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError(f"Username '{username}' already exists") from exc
        db.refresh(user)
        return user.id


def assign_course(username: str, course_code: str) -> None:
    """Link a lecturer to a course they teach."""
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            raise ValueError("User not found")
        if user.role != "lecturer":
            raise ValueError("Only users with the lecturer role can be assigned courses")

        course = db.scalar(select(Course).where(Course.code == course_code))
        if course is None:
            raise ValueError("Course not found")

        existing = db.scalar(
            select(LecturerCourse).where(
                LecturerCourse.user_id == user.id,
                LecturerCourse.course_id == course.id,
            )
        )
        if existing is not None:
            raise ValueError("Lecturer is already assigned to this course")

        db.add(LecturerCourse(user_id=user.id, course_id=course.id))
        db.commit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Early intervention administration commands")
    subcommands = parser.add_subparsers(dest="command", required=True)

    create = subcommands.add_parser("create-user", help="Create a user account")
    create.add_argument("--username", required=True)
    create.add_argument("--role", required=True, choices=ROLES)

    assign = subcommands.add_parser("assign-course", help="Link a lecturer to a course")
    assign.add_argument("--username", required=True)
    assign.add_argument("--course-code", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "create-user":
            username = args.username.strip().lower()
            user_id = create_user(username, args.role)
            print(f"Created user '{username}' with role '{args.role}' (id {user_id})")
        elif args.command == "assign-course":
            username = args.username.strip().lower()
            assign_course(username, args.course_code.strip())
            print(f"Assigned '{username}' to course '{args.course_code}'")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())