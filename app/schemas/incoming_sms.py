from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class IncomingSmsBase(BaseModel):
    channel_api_key: str
    provider: Optional[str] = None
    raw_message: str
    amount: Optional[int] = None
    currency: Optional[str] = "AED"
    txn_id: Optional[str] = None
    payer_phone: Optional[str] = None
    receiver_phone: Optional[str] = None
    timestamp: Optional[datetime] = None


class IncomingSmsCreate(IncomingSmsBase):
    """Payload used by Tasker/mobile webhook to send an incoming SMS."""
    pass


class IncomingSmsStored(BaseModel):
    payment_id: int
    status: str
