from fastapi import APIRouter, Depends

from app.auth import require_admin
from app.sheets import is_sheets_configured
from app.config import settings

router = APIRouter(
    prefix="/api/admin/config", tags=["admin-config"], dependencies=[Depends(require_admin)]
)


@router.get("")
def get_config():
    return {
        "sheets_configured": is_sheets_configured(),
        "service_account_email": settings.google_service_account_email or None,
    }
