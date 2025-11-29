from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class PaymentAdminSummary(BaseModel):
    payment_id: int
    company_id: int
    company_name: Optional[str] = None
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None
    wallet_id: Optional[int] = None
    txn_id: Optional[str] = None
    amount: int
    currency: str
    status: str
    payer_phone: Optional[str] = None
    created_at: datetime
    used_at: Optional[datetime] = None


class PaginatedPaymentsResponse(BaseModel):
    items: List[PaymentAdminSummary]
    total: int
    page: int
    page_size: int
