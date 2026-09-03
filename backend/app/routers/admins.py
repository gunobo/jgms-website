from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import CurrentUser, require_admin
from app.database import get_db
from app.models import Admin
from app.schemas import AdminCreate, AdminOut

router = APIRouter(
    prefix="/api/admin/admins", tags=["admins"], dependencies=[Depends(require_admin)]
)


@router.get("", response_model=list[AdminOut])
def list_admins(db: Session = Depends(get_db)):
    return db.query(Admin).order_by(Admin.created_at.asc()).all()


@router.post("", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
def create_admin(body: AdminCreate, db: Session = Depends(get_db)):
    admin = Admin(**body.model_dump())
    db.add(admin)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 관리자입니다."
        ) from exc
    db.refresh(admin)
    return admin


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(
    admin_id: str, db: Session = Depends(get_db), current: CurrentUser = Depends(require_admin)
):
    if db.query(Admin).count() <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="마지막 관리자는 삭제할 수 없습니다.")
    if current.user_id == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="본인 계정은 삭제할 수 없습니다. 다른 관리자에게 요청해주세요.",
        )
    admin = db.get(Admin, admin_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="관리자를 찾을 수 없습니다.")
    db.delete(admin)
    db.commit()
