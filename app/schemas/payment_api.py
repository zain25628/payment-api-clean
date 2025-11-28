from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class PaymentCheckRequest(BaseModel):
    order_id: str
    expected_amount: int
    txn_id: Optional[str] = None
    max_age_minutes: Optional[int] = 30


class PaymentMatchInfo(BaseModel):
    payment_id: int
    txn_id: Optional[str] = None
    amount: int
    currency: str
    created_at: datetime


class PaymentCheckResponse(BaseModel):
    found: bool
    match: bool
    reason: Optional[str] = None
    confirm_token: Optional[str] = None
    order_id: Optional[str] = None
    payment: Optional[PaymentMatchInfo] = None


class PaymentConfirmRequest(BaseModel):
    payment_id: int
    confirm_token: str


class PaymentConfirmResponse(BaseModel):
    success: bool
    already_used: bool = False
    payment_id: Optional[int] = None
    status: Optional[str] = None
