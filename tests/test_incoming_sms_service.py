import importlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.db.base import Base
from app.models.company import Company
from app.models.channel import Channel
from app.models.wallet import Wallet
from app.models.payment import Payment
from app.schemas.incoming_sms import IncomingSmsCreate
from app.services.incoming_sms_service import IncomingSmsService


def create_test_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Ensure all relevant models are registered on Base.metadata
    importlib.import_module("app.models.company")
    importlib.import_module("app.models.channel")
    importlib.import_module("app.models.wallet")
    importlib.import_module("app.models.payment")

    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_store_incoming_sms_creates_payment_and_links_company_channel():
    db = create_test_session()
    try:
        company = Company(name="Test Co", api_key="test-key")
        db.add(company)
        db.flush()

        channel = Channel(
            company_id=company.id,
            name="Test Channel",
            channel_api_key="chan-key-123",
        )
        db.add(channel)
        db.commit()

        data = IncomingSmsCreate(
            channel_api_key="chan-key-123",
            raw_message="تم تحويل 150 درهم",
            amount=150,
            currency="AED",
            txn_id="TXN123",
            payer_phone="0500000000",
            receiver_phone="0511111111",
        )

        payment = IncomingSmsService.store_incoming_sms(db, data)

        assert isinstance(payment, Payment)
        assert payment.company_id == company.id
        assert payment.channel_id == channel.id
        assert payment.amount == 150
        assert payment.currency == "AED"
        assert payment.raw_message.startswith("تم تحويل")
        assert payment.status == "new"
    finally:
        db.close()


def test_store_incoming_sms_raises_for_unknown_channel():
    db = create_test_session()
    try:
        data = IncomingSmsCreate(
            channel_api_key="unknown-key",
            raw_message="msg",
        )
        with pytest.raises(ValueError):
            IncomingSmsService.store_incoming_sms(db, data)
    finally:
        db.close()


def test_store_incoming_sms_links_wallet_when_receiver_phone_matches():
    db = create_test_session()
    try:
        company = Company(name="Test Co", api_key="test-key")
        db.add(company)
        db.flush()

        channel = Channel(
            company_id=company.id,
            name="Test Channel",
            channel_api_key="chan-key-123",
        )
        db.add(channel)
        db.flush()

        wallet = Wallet(
            company_id=company.id,
            channel_id=channel.id,
            wallet_label="Wallet #1",
            wallet_identifier="0511111111",
            daily_limit=500,
        )
        db.add(wallet)
        db.commit()

        data = IncomingSmsCreate(
            channel_api_key="chan-key-123",
            raw_message="تم تحويل 100 درهم",
            amount=100,
            receiver_phone="0511111111",
        )

        payment = IncomingSmsService.store_incoming_sms(db, data)

        assert payment.wallet_id == wallet.id
    finally:
        db.close()
