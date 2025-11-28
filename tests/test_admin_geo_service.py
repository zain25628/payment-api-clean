from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.country import Country, PaymentProvider, CountryPaymentProvider
from app.schemas.admin_geo import (
    AdminCountryOut,
    AdminPaymentProviderOut,
    AdminCountryWithProviders,
)
from app.services.admin_geo_service import AdminGeoService


def create_test_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_list_countries_returns_sorted_countries():
    db = create_test_session()
    try:
        c1 = Country(code="KSA", name="Saudi Arabia")
        c2 = Country(code="UAE", name="United Arab Emirates")
        db.add_all([c1, c2])
        db.commit()

        countries = AdminGeoService.list_countries(db)
        assert len(countries) == 2
        assert isinstance(countries[0], AdminCountryOut)
        assert countries[0].name <= countries[1].name
    finally:
        db.close()


def test_list_payment_providers_returns_sorted_providers():
    db = create_test_session()
    try:
        p1 = PaymentProvider(code="b_provider", name="B Provider")
        p2 = PaymentProvider(code="a_provider", name="A Provider")
        db.add_all([p1, p2])
        db.commit()

        providers = AdminGeoService.list_payment_providers(db)
        assert len(providers) == 2
        assert isinstance(providers[0], AdminPaymentProviderOut)
        assert providers[0].name <= providers[1].name
    finally:
        db.close()


def test_get_country_with_providers_returns_none_for_unknown_country():
    db = create_test_session()
    try:
        result = AdminGeoService.get_country_with_providers(db, country_code="XXX")
        assert result is None
    finally:
        db.close()


def test_get_country_with_providers_returns_country_and_supported_providers():
    db = create_test_session()
    try:
        country = Country(code="UAE", name="United Arab Emirates")
        p1 = PaymentProvider(code="eand_money", name="e& money")
        p2 = PaymentProvider(code="wallet_x", name="Wallet X")
        db.add_all([country, p1, p2])
        db.commit()

        link1 = CountryPaymentProvider(country_id=country.id, provider_id=p1.id, is_supported=True)
        link2 = CountryPaymentProvider(country_id=country.id, provider_id=p2.id, is_supported=False)
        db.add_all([link1, link2])
        db.commit()

        result = AdminGeoService.get_country_with_providers(db, country_code="UAE")
        assert isinstance(result, AdminCountryWithProviders)
        assert result.country.code == "UAE"
        assert len(result.providers) == 1
        assert result.providers[0].code == "eand_money"
    finally:
        db.close()
