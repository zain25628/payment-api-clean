from typing import Optional, List
from pydantic import BaseModel


class AdminPaymentProviderOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    country_code: Optional[str] = None

    model_config = {"from_attributes": True}


class AdminCountryOut(BaseModel):
    id: int
    code: str
    name: str

    model_config = {"from_attributes": True}


class AdminCountryCreate(BaseModel):
    code: str
    name: str

    model_config = {"from_attributes": True}


class AdminPaymentProviderCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    country_code: Optional[str] = None

    model_config = {"from_attributes": True}


class AdminCountryWithProviders(BaseModel):
    country: AdminCountryOut
    providers: List[AdminPaymentProviderOut]

    model_config = {"from_attributes": True}
