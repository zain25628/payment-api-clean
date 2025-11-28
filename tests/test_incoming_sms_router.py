from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.models.company import Company
from app.models.channel import Channel
from app.models.wallet import Wallet
from app.models.payment import Payment
from app.routers.incoming_sms import router as incoming_sms_router


def create_test_app_and_db():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Ensure models are registered
    import importlib
    importlib.import_module("app.models.company")
    importlib.import_module("app.models.channel")
    importlib.import_module("app.models.wallet")
    importlib.import_module("app.models.payment")
    # also import geo/payment provider models that other models FK to
    importlib.import_module("app.models.country")

    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(incoming_sms_router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    return app, TestingSessionLocal


def test_receive_incoming_sms_creates_payment_and_returns_stored_schema():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
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
    db.close()

    resp = client.post(
        "/incoming-sms/",
        headers={"X-API-Key": "test-key"},
        json={
            "channel_api_key": "chan-key-123",
            "raw_message": "تم تحويل 150 درهم",
            "amount": 150,
            "currency": "AED",
            "txn_id": "TXN123",
            "payer_phone": "0500000000",
            "receiver_phone": "0511111111",
        },
    )

    if resp.status_code not in (200, 201):
        print('DEBUG RESPONSE:', resp.status_code, resp.json())
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert "payment_id" in body
    # status may or may not be returned by existing route; verify either way
    if "status" in body:
        assert body["status"] == "new"

    db2 = SessionLocal()
    payment = db2.query(Payment).filter(Payment.id == body["payment_id"]).first()
    assert payment is not None
    assert payment.amount == 150
    assert payment.status == "new"
    db2.close()


def test_receive_incoming_sms_returns_400_for_invalid_channel_key():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    # create company so header is accepted, but do not create channel
    db = SessionLocal()
    company = Company(name="Test Co", api_key="test-key")
    db.add(company)
    db.commit()
    db.close()

    resp = client.post(
        "/incoming-sms/",
        headers={"X-API-Key": "test-key"},
        json={
            "channel_api_key": "wrong-key",
            "raw_message": "msg",
        },
    )

    if resp.status_code != 400:
        print('DEBUG RESPONSE:', resp.status_code, resp.json())
    assert resp.status_code == 400
    assert resp.json().get("detail") == "Invalid channel_api_key"


def test_receive_incoming_sms_links_wallet_if_exists():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
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
    wallet_id = wallet.id
    db.close()

    resp = client.post(
        "/incoming-sms/",
        headers={"X-API-Key": "test-key"},
        json={
            "channel_api_key": "chan-key-123",
            "raw_message": "تم تحويل 100 درهم",
            "amount": 100,
            "receiver_phone": "0511111111",
        },
    )
    if resp.status_code not in (200, 201):
        print('DEBUG RESPONSE:', resp.status_code, resp.json())
    assert resp.status_code in (200, 201)
    body = resp.json()
    payment_id = body["payment_id"]

    db2 = SessionLocal()
    payment = db2.query(Payment).filter(Payment.id == payment_id).first()
    assert payment is not None
    assert payment.wallet_id == wallet_id
    assert payment.status == "new"
    db2.close()
