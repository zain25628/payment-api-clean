from pydantic import BaseModel
from typing import List, Optional
from app.schemas.admin_wallets import AdminWalletOut


class AdminChannelOut(BaseModel):
    id: Optional[int] = None
    name: str
    provider_code: Optional[str] = None
    provider_name: Optional[str] = None
    channel_api_key: str
    telegram_group_id: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class AdminCompanyCreate(BaseModel):
    name: str
    country_code: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_default_group_id: Optional[str] = None
    provider_codes: List[str]

    model_config = {"from_attributes": True}


class AdminCompanyOut(BaseModel):
    id: int
    name: str
    api_key: str
    is_active: bool
    country_code: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_default_group_id: Optional[str] = None
    channels: List[AdminChannelOut] = []
    wallets: List[AdminWalletOut] = []

    model_config = {"from_attributes": True}


class AdminCompanyListItem(BaseModel):
    id: int
    name: str
    country_code: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}
