from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    admin_assignments,
    admin_config,
    admin_surveys,
    admins,
    assignments,
    auth,
    students,
    surveys,
)

app = FastAPI(title="창의적 소프트웨어 체험·활용반 사이트 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(admins.router)
app.include_router(admin_surveys.router)
app.include_router(surveys.router)
app.include_router(admin_assignments.router)
app.include_router(assignments.router)
app.include_router(admin_config.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
