from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Admin, Student

bearer_scheme = HTTPBearer(auto_error=False)

Role = Literal["admin", "student", "unregistered"]


class CurrentUser:
    def __init__(self, email: str, role: Role, user_id: str | None, name: str | None):
        self.email = email
        self.role = role
        self.user_id = user_id
        self.name = name


def verify_google_id_token(credential: str) -> dict:
    try:
        info = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), settings.google_client_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 구글 로그인입니다."
        ) from exc

    if settings.google_workspace_hd and info.get("hd") != settings.google_workspace_hd:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="학교 구글 계정으로만 로그인할 수 있습니다.",
        )

    return info


def create_access_token(email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _resolve_role(db: Session, email: str) -> CurrentUser:
    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin:
        return CurrentUser(email=email, role="admin", user_id=admin.id, name=admin.name or admin.email)

    student = db.query(Student).filter(Student.email == email).first()
    if student:
        return CurrentUser(email=email, role="student", user_id=student.id, name=student.name)

    if email in settings.admin_email_list:
        admin = Admin(email=email)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return CurrentUser(email=email, role="admin", user_id=admin.id, name=admin.email)

    return CurrentUser(email=email, role="unregistered", user_id=None, name=None)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="세션이 만료되었습니다. 다시 로그인해주세요."
        ) from exc

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")

    return _resolve_role(db, email)


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser | None:
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자만 접근할 수 있습니다.")
    return user


def require_student(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="학생 계정만 접근할 수 있습니다.")
    return user
