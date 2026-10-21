TERM = "2026-S1"
STUDENT_A = {"student_number": "S1001", "full_name": "Student A", "programme": "Computer Science"}
STUDENT_B = {"student_number": "S1002", "full_name": "Student B", "programme": "Computer Science"}
STUDENT_C = {"student_number": "S1003", "full_name": "Student C", "programme": "Computer Science"}
COURSE = {"code": "CS101", "title": "Intro"}


def create_student(admin, details) -> int:
    return admin.post("/students", json=details).json()["id"]


def setup_course(staff, link_lecturer, students):
    """Create a course, enrol the students for TERM, and link the lecturer to the course."""
    admin = staff["admin"]
    course_id = admin.post("/courses", json=COURSE).json()["id"]
    for student_id in students:
        admin.post(f"/students/{student_id}/enrolments", json={"course_id": course_id, "academic_term": TERM})
    link_lecturer(course_id)
    return course_id


def create_assignment(lecturer, course_id, title="Essay 1", term=TERM):
    return lecturer.post(
        "/assignments",
        json={"course_id": course_id, "academic_term": term, "title": title, "due_date": "2026-11-15"},
    )


def first_submission_id(lecturer, assignment_id):
    return lecturer.get(f"/assignments/{assignment_id}/submissions").json()[0]["id"]


def test_creating_assignment_creates_missing_rows_for_enrolled_students_only(staff, link_lecturer):
    admin = staff["admin"]
    student_a = create_student(admin, STUDENT_A)
    student_b = create_student(admin, STUDENT_B)
    student_c = create_student(admin, STUDENT_C)
    course_id = setup_course(staff, link_lecturer, [student_a, student_b])
    # Student C is enrolled in the course, but in a different term, so they must be excluded.
    admin.post(f"/students/{student_c}/enrolments", json={"course_id": course_id, "academic_term": "2026-S2"})

    lecturer = staff["lecturer"]
    assignment_id = create_assignment(lecturer, course_id).json()["id"]
    rows = lecturer.get(f"/assignments/{assignment_id}/submissions").json()

    assert sorted(row["student_id"] for row in rows) == sorted([student_a, student_b])
    assert all(row["status"] == "missing" for row in rows)
    assert all(row["submitted_on"] is None for row in rows)


def test_duplicate_assignment_title_returns_409(staff, link_lecturer):
    course_id = setup_course(staff, link_lecturer, [])
    lecturer = staff["lecturer"]
    create_assignment(lecturer, course_id)

    response = create_assignment(lecturer, course_id)

    assert response.status_code == 409


def test_assignment_for_missing_course_returns_404(staff, link_lecturer):
    setup_course(staff, link_lecturer, [])

    response = create_assignment(staff["lecturer"], course_id=999)

    assert response.status_code == 404


def test_unknown_assignment_returns_404(staff, link_lecturer):
    setup_course(staff, link_lecturer, [])
    lecturer = staff["lecturer"]

    assert lecturer.get("/assignments/999").status_code == 404
    assert lecturer.get("/assignments/999/submissions").status_code == 404


def test_submission_can_be_marked_submitted(staff, link_lecturer):
    student_id = create_student(staff["admin"], STUDENT_A)
    course_id = setup_course(staff, link_lecturer, [student_id])
    lecturer = staff["lecturer"]
    assignment_id = create_assignment(lecturer, course_id).json()["id"]
    submission_id = first_submission_id(lecturer, assignment_id)

    response = lecturer.put(
        f"/submissions/{submission_id}",
        json={"status": "submitted", "submitted_on": "2026-11-14"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "submitted"
    assert response.json()["submitted_on"] == "2026-11-14"


def test_missing_status_with_a_date_is_rejected(staff, link_lecturer):
    student_id = create_student(staff["admin"], STUDENT_A)
    course_id = setup_course(staff, link_lecturer, [student_id])
    lecturer = staff["lecturer"]
    assignment_id = create_assignment(lecturer, course_id).json()["id"]
    submission_id = first_submission_id(lecturer, assignment_id)

    response = lecturer.put(
        f"/submissions/{submission_id}",
        json={"status": "missing", "submitted_on": "2026-11-14"},
    )

    assert response.status_code == 422


def test_submitted_status_without_a_date_is_rejected(staff, link_lecturer):
    student_id = create_student(staff["admin"], STUDENT_A)
    course_id = setup_course(staff, link_lecturer, [student_id])
    lecturer = staff["lecturer"]
    assignment_id = create_assignment(lecturer, course_id).json()["id"]
    submission_id = first_submission_id(lecturer, assignment_id)

    response = lecturer.put(f"/submissions/{submission_id}", json={"status": "submitted"})

    assert response.status_code == 422


def test_unknown_submission_returns_404(staff, link_lecturer):
    setup_course(staff, link_lecturer, [])

    response = staff["lecturer"].put("/submissions/999", json={"status": "missing"})

    assert response.status_code == 404