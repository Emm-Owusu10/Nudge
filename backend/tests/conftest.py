import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app  # renamed so it doesn't clash with the package name
import app.models  # noqa: F401  (registers the models on Base.metadata)
from app.models.lecturer_course import LecturerCourse
from app.models.user import User

settings = get_settings()

# --- Safety checks -----------------------------------------------------------
# Tests delete all rows, so they must never run against the development database.
if not settings.test_database_url:
    raise RuntimeError("TEST_DATABASE_URL is not set in .env")

DEV_DATABASE_NAME = make_url(settings.database_url).database
TEST_DATABASE_NAME = make_url(settings.test_database_url).database

if TEST_DATABASE_NAME == DEV_DATABASE_NAME:
    raise RuntimeError("TEST_DATABASE_URL points to the development database. Refusing to run tests.")
if not TEST_DATABASE_NAME or not TEST_DATABASE_NAME.endswith("_test"):
    raise RuntimeError(
        f"Test database name must end with '_test' (got '{TEST_DATABASE_NAME}'). Refusing to run tests."
    )

test_engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

TEST_PASSWORD = "correct-horse-battery"

# Every table, child tables first. RESTART IDENTITY resets the id counters.
TRUNCATE_SQL = (
    "TRUNCATE audit_logs, lecturer_courses, users, interventions, flags, submissions, "
    "assignments, attendance, assessments, enrolments, students, courses RESTART IDENTITY CASCADE"
)


@pytest.fixture(scope="session", autouse=True)
def create_test_schema():
    """Confirm we are connected to the test database, then build the tables once."""
    with test_engine.connect() as connection:
        connected_database = connection.execute(text("SELECT current_database()")).scalar()
    if connected_database != TEST_DATABASE_NAME or not connected_database.endswith("_test"):
        raise RuntimeError(
            f"Connected to '{connected_database}', not a test database. Refusing to run tests."
        )

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """Empty every table before each test so tests don't affect each other."""
    with test_engine.begin() as connection:
        connection.execute(text(TRUNCATE_SQL))
    yield


def override_get_db():
    """Give the app a session on the test database."""
    db: Session = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def use_test_database():
    """Route every request in every test to the test database, so none can reach development data."""
    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client():
    """An unauthenticated client."""
    return TestClient(fastapi_app)


@pytest.fixture
def login_client():
    """Return a function that logs in as a username and returns a client carrying that token."""

    def _login(username: str, password: str = TEST_PASSWORD) -> TestClient:
        authenticated = TestClient(fastapi_app)
        response = authenticated.post(
            "/auth/login", json={"username": username, "password": password}
        )
        assert response.status_code == 200, response.text
        authenticated.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
        return authenticated

    return _login


@pytest.fixture
def db():
    """A database session on the test database, for tests that set up data directly."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def make_user():
    """Create a user in the test database. Returns make_user(username, password, role, is_active=True) -> user id."""

    def _make_user(username: str, password: str, role: str, is_active: bool = True) -> int:
        with TestingSessionLocal() as session:
            user = User(
                username=username,
                password_hash=hash_password(password),
                role=role,
                is_active=is_active,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user.id

    return _make_user


@pytest.fixture
def staff(make_user, login_client):
    """One logged-in administrator, advisor and lecturer, plus the lecturer's user id."""
    make_user("admin", TEST_PASSWORD, "administrator")
    make_user("advisor", TEST_PASSWORD, "advisor")
    lecturer_id = make_user("lecturer", TEST_PASSWORD, "lecturer")
    return {
        "admin": login_client("admin"),
        "advisor": login_client("advisor"),
        "lecturer": login_client("lecturer"),
        "lecturer_id": lecturer_id,
    }


@pytest.fixture
def link_lecturer(staff):
    """Return a function that links the test lecturer to a course they teach."""

    def _link(course_id: int) -> None:
        with TestingSessionLocal() as session:
            session.add(LecturerCourse(user_id=staff["lecturer_id"], course_id=course_id))
            session.commit()

    return _link