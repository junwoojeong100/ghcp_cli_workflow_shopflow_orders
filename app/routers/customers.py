from fastapi import APIRouter, Depends

from ..db import get_db
from ..schemas import CustomerOut, OrderOut
from ..services import order_service

router = APIRouter(tags=["customers"])


@router.get("/customers", response_model=list[CustomerOut])
def list_customers(db=Depends(get_db)):
    return order_service.list_customers(db)


@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db=Depends(get_db)):
    return order_service.get_customer(db, customer_id)


@router.get("/customers/{customer_id}/orders", response_model=list[OrderOut])
def list_customer_orders(customer_id: int, db=Depends(get_db)):
    order_service.get_customer(db, customer_id)
    return order_service.list_orders(db, customer_id)
