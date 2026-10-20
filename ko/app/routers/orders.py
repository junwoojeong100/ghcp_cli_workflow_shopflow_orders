from fastapi import APIRouter, Depends

from ..db import get_db
from ..schemas import OrderCreate, OrderOut, RefundCreate, RefundOut
from ..services import order_service, refund_service

router = APIRouter(tags=["orders"])


@router.post("/orders", response_model=OrderOut, status_code=201)
def create_order(body: OrderCreate, db=Depends(get_db)):
    return order_service.create_order(db, body)


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db=Depends(get_db)):
    return order_service.get_order(db, order_id)


@router.post("/orders/{order_id}/refund", response_model=RefundOut, status_code=201)
def request_refund(order_id: int, body: RefundCreate, db=Depends(get_db)):
    return refund_service.request_refund(db, order_id, body.amount)


@router.get("/refunds/{refund_id}", response_model=RefundOut)
def get_refund(refund_id: int, db=Depends(get_db)):
    return refund_service.get_refund(db, refund_id)
