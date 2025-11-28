import pytest
from app.models.company import Company


def test_company_basic_fields_present():
    company = Company(
        name="Test Co",
        api_key="test-key",
        country_code="UAE",
        telegram_bot_token="123:ABC",
        telegram_default_group_id="-1001234567890",
    )

    assert company.name == "Test Co"
    assert company.api_key == "test-key"
    assert company.country_code == "UAE"
    assert company.telegram_bot_token == "123:ABC"
    assert company.telegram_default_group_id == "-1001234567890"


def test_company_optional_fields_default_to_none():
    company = Company(name="Test Co", api_key="test-key")

    assert company.country_code is None
    assert company.telegram_bot_token is None
    assert company.telegram_default_group_id is None


def test_company_relationship_attributes_exist():
    company = Company(name="Test Co", api_key="test-key")

    # relationships should exist as attributes (SQLAlchemy sets them on instances)
    assert hasattr(company, "channels")
    assert hasattr(company, "wallets")
    assert hasattr(company, "payments")
