from typing import Optional
from pydantic import BaseModel


class AdminWalletBase(BaseModel):
    wallet_label: str
    wallet_identifier: str
    daily_limit: float
    is_active: bool = True
    channel_id: int


class AdminWalletCreate(AdminWalletBase):
    pass


class AdminWalletUpdate(BaseModel):
    wallet_label: Optional[str] = None
    wallet_identifier: Optional[str] = None
    daily_limit: Optional[float] = None
    is_active: Optional[bool] = None


class AdminWalletOut(BaseModel):
    id: int
    wallet_label: str
    wallet_identifier: str
    daily_limit: float
    is_active: bool
    channel_id: int
    channel_name: str
    provider_code: Optional[str] = None
    provider_name: Optional[str] = None

    model_config = {"from_attributes": True}
