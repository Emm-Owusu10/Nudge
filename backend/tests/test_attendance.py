TERM = "2026-S1"
STUDENT = {"student_number": "S1001", "full_name": "Test Student", "programme": "Computer Science"}
OTHER_STUDENT = {"student_number": "S2002", "full_name": "Other Student", "programme": "Biology"}
COURSE = {"code": "CS101", "title": "Introduction to Programming"}


def create_student(admin, details=STUDENT) -> int:
    return admin.post("/students", json=details).json()["id"]


def setup_course(staff, link_lecturer, students):
    """Create a course, enrol the students in it, and link the lecturer to it."""
    admin = staff["admin"]
    course_id = admin.post("/courses", json=COURSE).json()["id"]
    for student_id in students:
        admin.post(f"/students/{student_id}/enrolments", json={"course_id": course_id, "academic_term": TERM})
    link_lecturer(course_id)
    return course_id


def record(lecturer, student_id, course_id, day, status):
    return lecturer.post(
        f"/students/{student_id}/attendance",
        json={"course_id": course_id, "session_date": day, "status": status},
    )


def test_record_attendance_returns_201(staff, link_lecturer):
    student_id = create_student(staff["admin"])
    course_id = setup_course(staff, link_lecturer, [student_id])

    response = record(staff["lecturer"], student_id, course_id, "2026-09-01", "present")

    assert response.status_code == 201
    assert response.json()["status"] == "present"


def test_excused_is_accepted(staff, link_lecturer):
    student_id = create_student(staff["admin"])
    course_id = setup_course(staff, link_lecturer, [student_id])

    response = record(staff["lecturer"], student_id, course_id, "2026-09-01", "excused")

    assert response.status_code == 201


def test_duplicate_session_returns_409(staff, link_lecturer):
    student_id = create_student(staff["admin"])
    course_id = setup_course(staff, link_lecturer, [student_id])
    lecturer = staff["lecturer"]
    record(lecturer, student_id, course_id, "2026-09-01", "present")

    response = record(lecturer, student_id, course_id, "2026-09-01", "absent")

    assert response.status_code == 409


def test_unknown_status_is_rejected(staff, link_lecturer):
    student_id = create_student(staff["admin"])
    course_id = setup_course(staff, link_lecturer, [student_id])

    response = record(staff["lecturer"], student_id, course_id, "2026-09-01", "sick")

    assert response.status_code == 422


def test_attendance_for_missing_student_returns_404(staff, link_lecturer):
    course_id = setup_course(staff, link_lecturer, [])

    response = record(staff["lecturer"], 999, course_id, "2026-09-01", "present")

    assert response.status_code == 404


def test_list_attendance_returns_only_that_students_records(staff, link_lecturer):
    student_id = create_student(staff["admin"])
    other_id = create_student(staff["admin"], OTHER_STUDENT)
    course_id = setup_course(staff, link_lecturer, [student_id, other_id])
    lecturer = staff["lecturer"]
    record(lecturer, student_id, course_id, "2026-09-01", "present")
    record(lecturer, other_id, course_id, "2026-09-01", "absent")

    response = lecturer.get(f"/students/{student_id}/attendance")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["student_id"] == student_id