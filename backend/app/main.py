from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    assessments,
    assignments,
    attendance,
    audit,
    auth,
    courses,
    enrolments,
    flags,
    health,
    indicators,
    interventions,
    me,
    queue,
    students,
    submissions,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

# The React interface runs on Vite's default port. Only that origin may call the API
# from a browser. Logins use a bearer header, not cookies, so credentials stay off.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(audit.router)
app.include_router(me.router)
app.include_router(queue.router)
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(enrolments.router)
app.include_router(attendance.router)
app.include_router(assessments.router)
app.include_router(assignments.router)
app.include_router(submissions.router)
app.include_router(indicators.router)
app.include_router(flags.router)
app.include_router(interventions.router)