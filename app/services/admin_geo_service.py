from typing import List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.country import Country, PaymentProvider, CountryPaymentProvider
from app.schemas.admin_geo import (
    AdminCountryOut,
    AdminPaymentProviderOut,
    AdminCountryWithProviders,
    AdminCountryCreate,
    AdminPaymentProviderCreate,
)


class AdminGeoService:
    @staticmethod
    def list_countries(db: Session) -> List[AdminCountryOut]:
        """
        Return all countries as AdminCountryOut sorted by name.
        """
        countries = db.query(Country).order_by(Country.name.asc()).all()
        return [AdminCountryOut.model_validate(c) for c in countries]

    @staticmethod
    def list_payment_providers(db: Session) -> List[AdminPaymentProviderOut]:
        """
        Return all payment providers as AdminPaymentProviderOut sorted by name.
        """
        providers = db.query(PaymentProvider).order_by(PaymentProvider.name.asc()).all()
        return [AdminPaymentProviderOut.model_validate(p) for p in providers]

    @staticmethod
    def get_country_with_providers(db: Session, country_code: str) -> AdminCountryWithProviders | None:
        """
        Return a country and its supported payment providers by country code.

        - Looks up Country by its code (case-sensitive or case-insensitive as stored).
        - Joins CountryPaymentProvider and PaymentProvider.
        - Only includes providers where is_supported is True.
        - Returns None if the country is not found.
        """
        country: Country | None = (
            db.query(Country)
            .filter(Country.code == country_code)
            .first()
        )
        if country is None:
            return None

        links = (
            db.query(CountryPaymentProvider)
            .join(PaymentProvider, CountryPaymentProvider.provider_id == PaymentProvider.id)
            .filter(
                CountryPaymentProvider.country_id == country.id,
                CountryPaymentProvider.is_supported.is_(True),
            )
            .all()
        )

        providers_out: List[AdminPaymentProviderOut] = []
        for link in links:
            provider = link.provider
            providers_out.append(AdminPaymentProviderOut.model_validate(provider))

        country_out = AdminCountryOut.model_validate(country)
        return AdminCountryWithProviders(country=country_out, providers=providers_out)

    @staticmethod
    def create_country(db: Session, data: AdminCountryCreate) -> Country:
        """
        Create a new Country record.

        Raises HTTPException 400 if a country with the same code exists.
        """
        existing = db.query(Country).filter(Country.code == data.code).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Country code already exists")

        country = Country(code=data.code, name=data.name)
        db.add(country)
        db.commit()
        db.refresh(country)
        return country

    @staticmethod
    def create_payment_provider(db: Session, data: AdminPaymentProviderCreate) -> PaymentProvider:
        """
        Create a PaymentProvider and optionally link it to a Country via CountryPaymentProvider.

        Raises HTTPException 400 if provider code already exists.
        """
        # uniqueness check
        existing = db.query(PaymentProvider).filter(PaymentProvider.code == data.code).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider code already exists")

        provider = PaymentProvider(code=data.code, name=data.name, description=data.description)
        db.add(provider)
        db.flush()

        # optionally link to country
        if getattr(data, 'country_code', None):
            country = db.query(Country).filter(Country.code == data.country_code).first()
            if country:
                link = CountryPaymentProvider(country_id=country.id, provider_id=provider.id, is_supported=True)
                db.add(link)

        db.commit()
        db.refresh(provider)
        return provider
