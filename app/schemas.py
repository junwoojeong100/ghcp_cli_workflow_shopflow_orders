"""API 요청/응답 스키마."""

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    customer_id: int
    total_amount: int = Field(gt=0)
    status: str = "PAID"
    ordered_at: str | None = None  # YYYY-MM-DD, 생략하면 오늘


class RefundCreate(BaseModel):
    amount: int = Field(gt=0, description="환불 요청 금액(원)")


class CustomerOut(BaseModel):
    id: int
    name: str
    tier: str | None = None


class OrderOut(BaseModel):
    id: int
    customer_id: int
    total_amount: int
    status: str
    ordered_at: str


class RefundOut(BaseModel):
    id: int
    order_id: int
    amount: int
    status: str
    requested_at: str
    decided_at: str | None = None
