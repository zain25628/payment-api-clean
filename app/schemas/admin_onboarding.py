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
