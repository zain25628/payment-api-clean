from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.company import Company
from app.models.channel import Channel
from app.models.country import Country, PaymentProvider
from app.schemas.admin_company import AdminCompanyCreate
from app.services.admin_company_service import AdminCompanyService


def create_test_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # register tables
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_create_company_with_channels_creates_company_and_channels():
    db = create_test_session()
    try:
        provider1 = PaymentProvider(code="eand_money", name="e& money")
        provider2 = PaymentProvider(code="wallet_x", name="Wallet X")
        db.add_all([provider1, provider2])
        db.commit()

        data = AdminCompanyCreate(
            name="Test Co",
            country_code="UAE",
            provider_codes=["eand_money", "wallet_x"],
        )

        company = AdminCompanyService.create_company_with_channels(db, data)

        assert isinstance(company, Company)
        assert company.id is not None
        assert company.api_key and len(company.api_key) > 0

        channels = db.query(Channel).filter(Channel.company_id == company.id).all()
        assert len(channels) == 2
    finally:
        db.close()


def test_create_company_ignores_unknown_provider_codes():
    db = create_test_session()
    try:
        provider1 = PaymentProvider(code="eand_money", name="e& money")
        db.add(provider1)
        db.commit()

        data = AdminCompanyCreate(
            name="Test Co",
            country_code="UAE",
            provider_codes=["eand_money", "unknown_provider"],
        )

        company = AdminCompanyService.create_company_with_channels(db, data)
        channels = db.query(Channel).filter(Channel.company_id == company.id).all()
        assert len(channels) == 1
    finally:
        db.close()


def test_create_company_with_no_providers_creates_no_channels():
    db = create_test_session()
    try:
        data = AdminCompanyCreate(name="Test Co", country_code="UAE", provider_codes=[])
        company = AdminCompanyService.create_company_with_channels(db, data)
        assert isinstance(company, Company)
        channels = db.query(Channel).filter(Channel.company_id == company.id).all()
        assert len(channels) == 0
    finally:
        db.close()


def test_update_company_updates_fields_and_channels():
    db = create_test_session()
    try:
        provider1 = PaymentProvider(code="eand_money", name="e& money")
        provider2 = PaymentProvider(code="wallet_x", name="Wallet X")
        db.add_all([provider1, provider2])
        db.commit()

        create_data = AdminCompanyCreate(
            name="Initial Co",
            country_code="UAE",
            provider_codes=["eand_money"],
        )

        company = AdminCompanyService.create_company_with_channels(db, create_data)

        update_data = AdminCompanyCreate(
            name="Updated Co",
            country_code="KSA",
            telegram_bot_token="123:ABC",
            telegram_default_group_id="-100123",
            provider_codes=["wallet_x"],
        )

        updated = AdminCompanyService.update_company_and_channels(db, company.id, update_data)

        assert updated is not None
        assert updated.name == "Updated Co"
        assert updated.country_code == "KSA"
        assert updated.telegram_bot_token == "123:ABC"

        channels = db.query(Channel).filter(Channel.company_id == updated.id).all()

        # There should be a channel for wallet_x and it should be active
        wallet_channels = [c for c in channels if c.provider is not None and c.provider.code == "wallet_x"]
        assert len(wallet_channels) >= 1
        assert any(c.is_active for c in wallet_channels)

        # Existing channel for eand_money should be present but deactivated
        eand_channels = [c for c in channels if c.provider is not None and c.provider.code == "eand_money"]
        assert len(eand_channels) >= 1
        assert all(c.is_active is False for c in eand_channels)
    finally:
        db.close()


def test_update_company_unknown_id_returns_none():
    db = create_test_session()
    try:
        data = AdminCompanyCreate(name="NoCo", country_code="UAE", provider_codes=["eand_money"])
        result = AdminCompanyService.update_company_and_channels(db, company_id=9999, data=data)
        assert result is None
    finally:
        db.close()


def test_toggle_company_active_flips_flag():
    db = create_test_session()
    try:
        provider1 = PaymentProvider(code="eand_money", name="e& money")
        db.add(provider1)
        db.commit()

        data = AdminCompanyCreate(name="ToggleCo", country_code="UAE", provider_codes=["eand_money"])
        company = AdminCompanyService.create_company_with_channels(db, data)

        initial = company.is_active
        updated = AdminCompanyService.toggle_company_active(db, company.id)
        assert updated is not None
        assert updated.is_active != initial
    finally:
        db.close()
