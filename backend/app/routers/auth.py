from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import CurrentUser, create_access_token, get_current_user, verify_google_id_token
from app.database import get_db
from app.schemas import GoogleLoginIn, MeOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/google")
def google_login(body: GoogleLoginIn, db: Session = Depends(get_db)):
    info = verify_google_id_token(body.credential)
    email = info["email"]
    token = create_access_token(email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=MeOut)
def me(user: CurrentUser = Depends(get_current_user)):
    return MeOut(email=user.email, role=user.role, name=user.name, user_id=user.user_id)
