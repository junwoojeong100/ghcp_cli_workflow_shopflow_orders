"""API request/response schemas."""

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    customer_id: int
    total_amount: int = Field(gt=0)
    status: str = "PAID"
    ordered_at: str | None = None  # YYYY-MM-DD; defaults to today if omitted


class RefundCreate(BaseModel):
    amount: int = Field(gt=0, description="Requested refund amount (KRW)")


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
