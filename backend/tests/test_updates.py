TERM = "2026-S1"
STUDENT = {"student_number": "S1001", "full_name": "Test Student", "programme": "Computer Science"}
OTHER_STUDENT = {"student_number": "S2002", "full_name": "Other Student", "programme": "Biology"}
COURSE = {"code": "CS101", "title": "Introduction to Programming"}


def setup(staff, link_lecturer, extra_students=()):
    """Create a student and a course, enrol the student and any extras, and link the lecturer.

    Returns (student_id, course_id).
    """
    admin = staff["admin"]
    student_id = admin.post("/students", json=STUDENT).json()["id"]
    course_id = admin.post("/courses", json=COURSE).json()["id"]
    admin.post(f"/students/{student_id}/enrolments", json={"course_id": course_id, "academic_term": TERM})
    for extra_id in extra_students:
        admin.post(f"/students/{extra_id}/enrolments", json={"course_id": course_id, "academic_term": TERM})
    link_lecturer(course_id)
    return student_id, course_id


# --- Students (administrator only) ------------------------------------------

def test_student_name_can_be_corrected(staff, link_lecturer):
    student_id, _ = setup(staff, link_lecturer)

    response = staff["admin"].patch(f"/students/{student_id}", json={"full_name": "Corrected Name"})

    assert response.status_code == 200
    assert response.json()["full_name"] == "Corrected Name"
    assert response.json()["student_number"] == "S1001"


def test_student_number_cannot_be_changed(staff, link_lecturer):
    student_id, _ = setup(staff, link_lecturer)

    response = staff["admin"].patch(f"/students/{student_id}", json={"student_number": "S9999"})

    assert response.status_code == 422


def test_empty_update_is_rejected(staff, link_lecturer):
    student_id, _ = setup(staff, link_lecturer)

    response = staff["admin"].patch(f"/students/{student_id}", json={})

    assert response.status_code == 422


def test_explicit_null_is_rejected(staff, link_lecturer):
    student_id, _ = setup(staff, link_lecturer)

    response = staff["admin"].patch(f"/students/{student_id}", json={"full_name": None})

    assert response.status_code == 422


def test_updating_missing_student_returns_404(staff):
    response = staff["admin"].patch("/students/999", json={"full_name": "Nobody"})

    assert response.status_code == 404


# --- Courses (administrator only) -------------------------------------------

def test_course_title_can_be_corrected(staff, link_lecturer):
    _, course_id = setup(staff, link_lecturer)

    response = staff["admin"].patch(f"/courses/{course_id}", json={"title": "Programming Fundamentals"})

    assert response.status_code == 200
    assert response.json()["title"] == "Programming Fundamentals"
    assert response.json()["code"] == "CS101"


def test_course_code_cannot_be_changed(staff, link_lecturer):
    _, course_id = setup(staff, link_lecturer)

    response = staff["admin"].patch(f"/courses/{course_id}", json={"code": "CS999"})

    assert response.status_code == 422


# --- Attendance (lecturer, own courses) -------------------------------------

def test_attendance_status_can_be_corrected_and_date_is_kept(staff, link_lecturer):
    student_id, course_id = setup(staff, link_lecturer)
    lecturer = staff["lecturer"]
    record = lecturer.post(
        f"/students/{student_id}/attendance",
        json={"course_id": course_id, "session_date": "2026-09-01", "status": "present"},
    ).json()

    response = lecturer.patch(f"/students/{student_id}/attendance/{record['id']}", json={"status": "absent"})

    assert response.status_code == 200
    assert response.json()["status"] == "absent"
    assert response.json()["session_date"] == "2026-09-01"


def test_attendance_status_must_still_be_valid(staff, link_lecturer):
    student_id, course_id = setup(staff, link_lecturer)
    lecturer = staff["lecturer"]
    record = lecturer.post(
        f"/students/{student_id}/attendance",
        json={"course_id": course_id, "session_date": "2026-09-01", "status": "present"},
    ).json()

    response = lecturer.patch(f"/students/{student_id}/attendance/{record['id']}", json={"status": "sick"})

    assert response.status_code == 422


def test_attendance_belonging_to_another_student_returns_404(staff, link_lecturer):
    admin = staff["admin"]
    lecturer = staff["lecturer"]
    other_id = admin.post("/students", json=OTHER_STUDENT).json()["id"]
    student_id, course_id = setup(staff, link_lecturer, extra_students=[other_id])
    record = lecturer.post(
        f"/students/{other_id}/attendance",
        json={"course_id": course_id, "session_date": "2026-09-01", "status": "present"},
    ).json()

    response = lecturer.patch(f"/students/{student_id}/attendance/{record['id']}", json={"status": "absent"})

    assert response.status_code == 404


# --- Assessments (lecturer, own courses) ------------------------------------

def test_assessment_score_can_be_corrected(staff, link_lecturer):
    student_id, course_id = setup(staff, link_lecturer)
    lecturer = staff["lecturer"]
    record = lecturer.post(
        f"/students/{student_id}/assessments",
        json={"course_id": course_id, "title": "Midterm", "assessed_on": "2026-10-01", "score": 55},
    ).json()

    response = lecturer.patch(f"/students/{student_id}/assessments/{record['id']}", json={"score": 61})

    assert response.status_code == 200
    assert response.json()["score"] == 61
    assert response.json()["title"] == "Midterm"


def test_assessment_score_must_stay_within_range(staff, link_lecturer):
    student_id, course_id = setup(staff, link_lecturer)
    lecturer = staff["lecturer"]
    record = lecturer.post(
        f"/students/{student_id}/assessments",
        json={"course_id": course_id, "title": "Midterm", "assessed_on": "2026-10-01", "score": 55},
    ).json()

    response = lecturer.patch(f"/students/{student_id}/assessments/{record['id']}", json={"score": 150})

    assert response.status_code == 422


def test_assessment_course_cannot_be_changed(staff, link_lecturer):
    student_id, course_id = setup(staff, link_lecturer)
    lecturer = staff["lecturer"]
    record = lecturer.post(
        f"/students/{student_id}/assessments",
        json={"course_id": course_id, "title": "Midterm", "assessed_on": "2026-10-01", "score": 55},
    ).json()

    response = lecturer.patch(f"/students/{student_id}/assessments/{record['id']}", json={"course_id": 999})

    assert response.status_code == 422