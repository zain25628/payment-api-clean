from app.schemas.admin_company import (
    AdminChannelOut,
    AdminCompanyCreate,
    AdminCompanyOut,
    AdminCompanyListItem,
)


def test_admin_company_create_requires_name_and_providers():
    data = AdminCompanyCreate(
        name="Test Co",
        country_code="UAE",
        telegram_bot_token="123:ABC",
        telegram_default_group_id="-1001234567890",
        provider_codes=["eand_money", "wallet_x"],
    )

    assert data.name == "Test Co"
    assert data.country_code == "UAE"
    assert len(data.provider_codes) == 2


def test_admin_company_out_with_channels():
    ch1 = AdminChannelOut(
        id=1,
        name="C1",
        provider_code="eand_money",
        provider_name="e& money",
        channel_api_key="k1",
        telegram_group_id="-100123",
        is_active=True,
    )
    ch2 = AdminChannelOut(
        id=2,
        name="C2",
        provider_code="wallet_x",
        provider_name="Wallet X",
        channel_api_key="k2",
        telegram_group_id=None,
        is_active=False,
    )

    comp = AdminCompanyOut(
        id=10,
        name="TestCo",
        api_key="ak",
        is_active=True,
        channels=[ch1, ch2],
    )

    assert len(comp.channels) == 2
    assert comp.id == 10
    assert comp.name == "TestCo"
    assert comp.api_key == "ak"


def test_admin_company_list_item_basic():
    item = AdminCompanyListItem(id=1, name="Test", country_code="UAE", is_active=True)
    assert item.id == 1
    assert item.name == "Test"
    assert item.country_code == "UAE"

    item2 = AdminCompanyListItem(id=2, name="NoCountry", country_code=None, is_active=False)
    assert item2.country_code is None
