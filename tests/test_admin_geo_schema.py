from app.schemas.admin_geo import (
    AdminCountryOut,
    AdminPaymentProviderOut,
    AdminCountryWithProviders,
)


def test_admin_payment_provider_out_basic():
    provider = AdminPaymentProviderOut(
        id=1,
        code="eand_money",
        name="e& money",
        description="Wallet provider",
    )

    assert provider.id == 1
    assert provider.code == "eand_money"
    assert provider.name == "e& money"
    assert provider.description == "Wallet provider"


def test_admin_country_out_basic():
    country = AdminCountryOut(
        id=1,
        code="UAE",
        name="United Arab Emirates",
    )

    assert country.id == 1
    assert country.code == "UAE"
    assert country.name == "United Arab Emirates"


def test_admin_country_with_providers_composition():
    country = AdminCountryOut(id=1, code="UAE", name="United Arab Emirates")
    p1 = AdminPaymentProviderOut(id=10, code="eand_money", name="e& money", description="desc1")
    p2 = AdminPaymentProviderOut(id=11, code="wallet_x", name="Wallet X", description=None)

    obj = AdminCountryWithProviders(country=country, providers=[p1, p2])

    assert obj.country.code == "UAE"
    assert len(obj.providers) == 2
    assert obj.providers[0].code == "eand_money"
    assert obj.providers[1].name == "Wallet X"
