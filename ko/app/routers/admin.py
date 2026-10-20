from fastapi import APIRouter, Depends, Header, HTTPException

from .. import config
from ..db import get_db
from ..schemas import RefundOut
from ..services import refund_service

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_token: str | None = Header(default=None)) -> str:
    if x_admin_token != config.admin_token():
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "관리자 인증이 필요합니다."},
        )
    return "admin"


@router.get("/refunds", response_model=list[RefundOut])
def list_refunds(status: str | None = None, db=Depends(get_db), _: str = Depends(require_admin)):
    return refund_service.list_refunds(db, status)


@router.post("/refunds/{refund_id}/approve", response_model=RefundOut)
def approve_refund(refund_id: int, db=Depends(get_db), actor: str = Depends(require_admin)):
    return refund_service.decide_refund(db, refund_id, approve=True, actor=actor)


@router.post("/refunds/{refund_id}/reject", response_model=RefundOut)
def reject_refund(refund_id: int, db=Depends(get_db), actor: str = Depends(require_admin)):
    return refund_service.decide_refund(db, refund_id, approve=False, actor=actor)
