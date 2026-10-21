VALID_STUDENT = {"student_number": "S1001", "full_name": "Test Student", "programme": "Computer Science"}


def test_create_student_returns_201_and_the_record(staff):
    response = staff["admin"].post("/students", json=VALID_STUDENT)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["student_number"] == "S1001"
    assert "created_at" in body


def test_duplicate_student_number_returns_409(staff):
    admin = staff["admin"]
    admin.post("/students", json=VALID_STUDENT)

    response = admin.post("/students", json={**VALID_STUDENT, "full_name": "Someone Else"})

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_blank_full_name_is_rejected(staff):
    response = staff["admin"].post("/students", json={**VALID_STUDENT, "full_name": "   "})

    assert response.status_code == 422


def test_student_number_with_invalid_characters_is_rejected(staff):
    response = staff["admin"].post(
        "/students", json={**VALID_STUDENT, "student_number": "S1001; DROP"}
    )

    assert response.status_code == 422


def test_unknown_field_is_rejected(staff):
    response = staff["admin"].post("/students", json={**VALID_STUDENT, "id": 99})

    assert response.status_code == 422


def test_surrounding_spaces_are_removed_from_student_number(staff):
    response = staff["admin"].post(
        "/students", json={**VALID_STUDENT, "student_number": "  S2002  "}
    )

    assert response.status_code == 201
    assert response.json()["student_number"] == "S2002"


def test_missing_student_returns_404(staff):
    response = staff["admin"].get("/students/999")

    assert response.status_code == 404


def test_non_integer_id_returns_422(staff):
    response = staff["admin"].get("/students/abc")

    assert response.status_code == 422


def test_limit_above_maximum_is_rejected(staff):
    response = staff["admin"].get("/students", params={"limit": 500})

    assert response.status_code == 422