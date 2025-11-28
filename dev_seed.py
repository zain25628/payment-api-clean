import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def main():
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

    engine = create_engine(DATABASE_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    # import Base and models so metadata is populated
    from app.db.base import Base
    from app.models.country import Country, PaymentProvider, CountryPaymentProvider
    from app.models.company import Company
    from app.models.channel import Channel

    # create tables if missing
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # 1) create country
        country = db.query(Country).filter(Country.code == "UAE").first()
        if not country:
            country = Country(code="UAE", name="United Arab Emirates")
            db.add(country)
            db.flush()

        # 2) create provider
        provider = (
            db.query(PaymentProvider)
            .filter(PaymentProvider.code == "eand_money")
            .first()
        )
        if not provider:
            provider = PaymentProvider(
                code="eand_money",
                name="e& money",
                description="Dev seed provider",
            )
            db.add(provider)
            db.flush()

        # 3) link country + provider
        link = (
            db.query(CountryPaymentProvider)
            .filter(
                CountryPaymentProvider.country_id == country.id,
                CountryPaymentProvider.provider_id == provider.id,
            )
            .first()
        )
        if not link:
            link = CountryPaymentProvider(
                country_id=country.id,
                provider_id=provider.id,
                is_supported=True,
            )
            db.add(link)

        # 4) create company (مع ضبط created_at / updated_at يدوياً لتفادي now() في SQLite)
        company = (
            db.query(Company)
            .filter(Company.api_key == "dev-api-key")
            .first()
        )
        if not company:
            company = Company(
                name="Dev Co",
                country_code="UAE",
                is_active=True,
                api_key="dev-api-key",
                created_at=now,
                updated_at=now,
            )
            db.add(company)
            db.flush()

        # 5) create channel (أيضاً نضبط created_at / updated_at)
        channel = (
            db.query(Channel)
            .filter(
                Channel.company_id == company.id,
                Channel.provider_id == provider.id,
            )
            .first()
        )
        if not channel:
            channel = Channel(
                company_id=company.id,
                provider_id=provider.id,
                name="Dev e& money",
                channel_api_key="dev-channel-key",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(channel)

        db.commit()

        print("Seed completed ✅")
        print(f"Database URL: {DATABASE_URL}")
        print("X-API-Key (company): dev-api-key")
        print("channel_api_key (channel): dev-channel-key")

    finally:
        db.close()


if __name__ == "__main__":
    main()
