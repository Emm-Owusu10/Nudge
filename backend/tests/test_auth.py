from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings

PASSWORD = "correct-horse-battery"


def login(client, username: str, password: str):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_login_returns_token_for_valid_credentials(client, make_user):
    make_user("advisor.one", PASSWORD, "advisor")

    response = login(client, "advisor.one", PASSWORD)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] == get_settings().access_token_minutes * 60


def test_wrong_password_returns_401(client, make_user):
    make_user("advisor.one", PASSWORD, "advisor")

    response = login(client, "advisor.one", "wrong-password-value")

    assert response.status_code == 401


def test_unknown_user_gets_the_same_response_as_a_wrong_password(client, make_user):
    make_user("advisor.one", PASSWORD, "advisor")

    wrong_password = login(client, "advisor.one", "wrong-password-value")
    unknown_user = login(client, "nobody.here", PASSWORD)

    assert unknown_user.status_code == 401
    assert unknown_user.json() == wrong_password.json()


def test_inactive_user_cannot_log_in(client, make_user):
    make_user("former.staff", PASSWORD, "lecturer", is_active=False)

    response = login(client, "former.staff", PASSWORD)

    assert response.status_code == 401


def test_me_without_a_token_returns_401(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_with_a_valid_token_returns_the_user(client, make_user):
    make_user("lecturer.one", PASSWORD, "lecturer")
    token = login(client, "lecturer.one", PASSWORD).json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "lecturer.one"
    assert body["role"] == "lecturer"
    assert "password_hash" not in body


def test_tampered_token_is_rejected(client, make_user):
    user_id = make_user("lecturer.one", PASSWORD, "lecturer")
    # Signed with a different key, so the signature check must fail.
    forged = jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
        "x" * 40,
        algorithm="HS256",
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


def test_expired_token_is_rejected(client, make_user):
    user_id = make_user("lecturer.one", PASSWORD, "lecturer")
    settings = get_settings()
    expired = jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})

    assert response.status_code == 401