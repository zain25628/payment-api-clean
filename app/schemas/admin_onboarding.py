from pydantic import BaseModel
from typing import List


class MerchantOnboardingExample(BaseModel):
    language: str
    title: str
    snippet: str


class MerchantOnboardingInfo(BaseModel):
    base_url: str
    docs_url: str
    api_key: str
    examples: List[MerchantOnboardingExample] = []

    model_config = {"from_attributes": True}


class AdminOnboardingGenerateResponse(BaseModel):
    company_id: int
    html_path: str
    pdf_path: str | None = None
    html_url: str
    pdf_url: str | None = None
    environment: str
