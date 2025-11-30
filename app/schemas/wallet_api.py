from pydantic import BaseModel, Field
from typing import Optional


class WalletRequestPayload(BaseModel):
    amount: int = Field(..., gt=0)
    currency: str = "AED"
    order_id: Optional[str] = None
    provider_code: Optional[str] = None
    preferred_payment_method: Optional[str] = Field(
        default=None,
        description="Optional provider slug; if set, wallet selection is restricted to this payment method.",
    )


class WalletRequestResponse(BaseModel):
    wallet_identifier: str
    wallet_label: str
    channel_api_key: str
    channel_id: int
    wallet_id: int

    class Config:
        orm_mode = True
