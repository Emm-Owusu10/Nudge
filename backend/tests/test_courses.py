VALID_COURSE = {"code": "CS101", "title": "Introduction to Programming"}


def test_create_course_returns_201_and_the_record(staff):
    response = staff["admin"].post("/courses", json=VALID_COURSE)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["code"] == "CS101"
    assert body["title"] == "Introduction to Programming"


def test_duplicate_course_code_returns_409(staff):
    admin = staff["admin"]
    admin.post("/courses", json=VALID_COURSE)

    response = admin.post("/courses", json={**VALID_COURSE, "title": "Another Title"})

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_course_code_with_invalid_characters_is_rejected(staff):
    response = staff["admin"].post("/courses", json={**VALID_COURSE, "code": "CS 101!"})

    assert response.status_code == 422


def test_blank_title_is_rejected(staff):
    response = staff["admin"].post("/courses", json={**VALID_COURSE, "title": "   "})

    assert response.status_code == 422


def test_unknown_field_is_rejected(staff):
    response = staff["admin"].post("/courses", json={**VALID_COURSE, "id": 99})

    assert response.status_code == 422


def test_missing_course_returns_404(staff):
    response = staff["admin"].get("/courses/999")

    assert response.status_code == 404


def test_list_courses_returns_created_courses(staff):
    admin = staff["admin"]
    admin.post("/courses", json=VALID_COURSE)
    admin.post("/courses", json={"code": "MATH200", "title": "Calculus"})

    response = staff["advisor"].get("/courses")

    assert response.status_code == 200
    assert [course["code"] for course in response.json()] == ["CS101", "MATH200"]