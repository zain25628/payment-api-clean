from app.models.country import Country, PaymentProvider, CountryPaymentProvider


def test_create_country_and_provider_link():
    country = Country(code="UAE", name="United Arab Emirates")
    provider = PaymentProvider(code="eand_money", name="e& money")

    link = CountryPaymentProvider(country=country, provider=provider, is_supported=True)

    assert link.country is country
    assert link.provider is provider
    assert link.is_supported is True


def test_country_has_country_providers_relationship():
    country = Country(code="UAE", name="United Arab Emirates")
    provider = PaymentProvider(code="eand_money", name="e& money")
    link = CountryPaymentProvider(country=country, provider=provider)

    assert len(country.country_providers) == 1
    assert country.country_providers[0] is link


def test_provider_has_country_links_relationship():
    country = Country(code="UAE", name="United Arab Emirates")
    provider = PaymentProvider(code="eand_money", name="e& money")
    link = CountryPaymentProvider(country=country, provider=provider)

    assert len(provider.country_links) == 1
    assert provider.country_links[0] is link
