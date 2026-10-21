TERM = "2026-S1"
STUDENT = {"student_number": "S1001", "full_name": "Test Student", "programme": "Computer Science"}
OTHER_STUDENT = {"student_number": "S2002", "full_name": "Other Student", "programme": "Biology"}
COURSE = {"code": "CS101", "title": "Introduction to Programming"}


def create_student_and_course(admin):
    """Helper: create one student and one course, returning their ids."""
    student_id = admin.post("/students", json=STUDENT).json()["id"]
    course_id = admin.post("/courses", json=COURSE).json()["id"]
    return student_id, course_id


def test_enrol_student_returns_201(staff):
    student_id, course_id = create_student_and_course(staff["admin"])

    response = staff["admin"].post(
        f"/students/{student_id}/enrolments",
        json={"course_id": course_id, "academic_term": TERM},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["student_id"] == student_id
    assert body["course_id"] == course_id
    assert body["academic_term"] == TERM


def test_duplicate_enrolment_in_same_term_returns_409(staff):
    admin = staff["admin"]
    student_id, course_id = create_student_and_course(admin)
    payload = {"course_id": course_id, "academic_term": TERM}
    admin.post(f"/students/{student_id}/enrolments", json=payload)

    response = admin.post(f"/students/{student_id}/enrolments", json=payload)

    assert response.status_code == 409


def test_same_course_in_different_term_is_allowed(staff):
    admin = staff["admin"]
    student_id, course_id = create_student_and_course(admin)
    admin.post(f"/students/{student_id}/enrolments", json={"course_id": course_id, "academic_term": "2026-S1"})

    response = admin.post(
        f"/students/{student_id}/enrolments",
        json={"course_id": course_id, "academic_term": "2026-S2"},
    )

    assert response.status_code == 201


def test_enrolling_missing_student_returns_404(staff):
    _, course_id = create_student_and_course(staff["admin"])

    response = staff["admin"].post(
        "/students/999/enrolments",
        json={"course_id": course_id, "academic_term": TERM},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_enrolling_in_missing_course_returns_404(staff):
    admin = staff["admin"]
    student_id = admin.post("/students", json=STUDENT).json()["id"]

    response = admin.post(
        f"/students/{student_id}/enrolments",
        json={"course_id": 999, "academic_term": TERM},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Course not found"


def test_invalid_term_format_is_rejected(staff):
    admin = staff["admin"]
    student_id, course_id = create_student_and_course(admin)

    response = admin.post(
        f"/students/{student_id}/enrolments",
        json={"course_id": course_id, "academic_term": "Spring 26"},
    )

    assert response.status_code == 422


def test_list_enrolments_returns_only_that_students_records(staff):
    admin = staff["admin"]
    student_id, course_id = create_student_and_course(admin)
    other_id = admin.post("/students", json=OTHER_STUDENT).json()["id"]
    admin.post(f"/students/{student_id}/enrolments", json={"course_id": course_id, "academic_term": TERM})
    admin.post(f"/students/{other_id}/enrolments", json={"course_id": course_id, "academic_term": TERM})

    response = admin.get(f"/students/{student_id}/enrolments")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["student_id"] == student_id