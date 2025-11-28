import importlib
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db

from app.routers.incoming_sms import router as incoming_sms_router
from app.routers.payments import router as payments_router
from app.routers.admin_companies import router as admin_companies_router
from app.routers.admin_geo import router as admin_geo_router


def create_test_app_and_db():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # ensure models are imported (so metadata contains them)
    importlib.import_module("app.models.company")
    importlib.import_module("app.models.channel")
    importlib.import_module("app.models.wallet")
    importlib.import_module("app.models.payment")
    importlib.import_module("app.models.country")

    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(incoming_sms_router)
    app.include_router(payments_router)
    app.include_router(admin_companies_router)
    app.include_router(admin_geo_router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    return app, TestingSessionLocal, engine


def test_full_flow_happy_path():
    app, SessionLocal, engine = create_test_app_and_db()
    client = TestClient(app)

    # create country + provider + link
    db = SessionLocal()
    from app.models.country import Country, PaymentProvider, CountryPaymentProvider

    country = Country(code="UAE", name="United Arab Emirates")
    provider = PaymentProvider(code="eand_money", name="e& money")
    db.add_all([country, provider])
    db.flush()

    link = CountryPaymentProvider(country_id=country.id, provider_id=provider.id)
    db.add(link)
    db.commit()
    db.close()

    # create company via admin endpoint
    resp = client.post(
        "/admin/companies",
        json={
            "name": "Flow Co",
            "country_code": "UAE",
            "provider_codes": ["eand_money"],
        },
    )
    assert resp.status_code == 201
    created = resp.json()
    company_id = created["id"]
    api_key = created["api_key"]
    assert created.get("channels") and len(created["channels"]) >= 1
    channel_api_key = created["channels"][0].get("channel_api_key")

    # send incoming SMS
    sms_resp = client.post(
        "/incoming-sms/",
        headers={"X-API-Key": api_key},
        json={
            "channel_api_key": channel_api_key,
            "raw_message": "تم تحويل 150 درهم",
            "amount": 150,
            "currency": "AED",
            "txn_id": "TXN123",
            "payer_phone": "0500000000",
            "receiver_phone": "0511111111",
        },
    )
    assert sms_resp.status_code in (200, 201)
    body = sms_resp.json()
    assert "payment_id" in body
    payment_id = body["payment_id"]
    if "status" in body:
        assert body["status"] == "new"

    # check payment (merchant site)
    check_resp = client.post(
        "/payments/check",
        headers={"X-API-Key": api_key},
        json={
            "order_id": "ORD-123",
            "expected_amount": 150,
            "txn_id": "TXN123",
        },
    )
    assert check_resp.status_code == 200
    check_data = check_resp.json()
    assert check_data["found"] is True
    assert check_data["match"] is True
    token = check_data.get("confirm_token")
    assert token is not None
    assert check_data["payment"]["payment_id"] == payment_id

    # confirm payment
    confirm_resp1 = client.post(
        "/payments/confirm",
        headers={"X-API-Key": api_key},
        json={"payment_id": payment_id, "confirm_token": token},
    )
    assert confirm_resp1.status_code == 200
    b1 = confirm_resp1.json()
    assert b1["success"] is True
    assert b1["already_used"] is False
    assert b1["status"] == "used"

    # idempotent second confirm
    confirm_resp2 = client.post(
        "/payments/confirm",
        headers={"X-API-Key": api_key},
        json={"payment_id": payment_id, "confirm_token": token},
    )
    assert confirm_resp2.status_code == 200
    b2 = confirm_resp2.json()
    assert b2["success"] is True
    assert b2["already_used"] is True
    assert b2["status"] == "used"


def test_check_mismatch_amount():
    app, SessionLocal, engine = create_test_app_and_db()
    client = TestClient(app)

    # setup country/provider/company
    db = SessionLocal()
    from app.models.country import Country, PaymentProvider, CountryPaymentProvider

    country = Country(code="UAE", name="United Arab Emirates")
    provider = PaymentProvider(code="eand_money", name="e& money")
    db.add_all([country, provider])
    db.flush()
    db.add(CountryPaymentProvider(country_id=country.id, provider_id=provider.id))
    db.commit()
    db.close()

    resp = client.post(
        "/admin/companies",
        json={"name": "Flow Co", "country_code": "UAE", "provider_codes": ["eand_money"]},
    )
    assert resp.status_code == 201
    created = resp.json()
    api_key = created["api_key"]
    channel_api_key = created["channels"][0]["channel_api_key"]

    # incoming sms amount 150
    sms_resp = client.post(
        "/incoming-sms/",
        headers={"X-API-Key": api_key},
        json={
            "channel_api_key": channel_api_key,
            "raw_message": "تم تحويل 150 درهم",
            "amount": 150,
            "currency": "AED",
            "txn_id": "TXN123",
            "payer_phone": "0500000000",
            "receiver_phone": "0511111111",
        },
    )
    assert sms_resp.status_code in (200, 201)
    payment_id = sms_resp.json()["payment_id"]

    # check with expected_amount 200 -> mismatch
    check_resp = client.post(
        "/payments/check",
        headers={"X-API-Key": api_key},
        json={"order_id": "ORD-123", "expected_amount": 200, "txn_id": "TXN123"},
    )
    assert check_resp.status_code == 200
    data = check_resp.json()
    assert data["found"] is True
    assert data["match"] is False
    assert data.get("reason") == "amount_mismatch"
    assert data.get("confirm_token") is None


def test_check_not_found_for_old_payment():
    app, SessionLocal, engine = create_test_app_and_db()
    client = TestClient(app)

    # create company + payment manually
    db = SessionLocal()
    from app.models.company import Company
    from app.models.payment import Payment

    company = Company(name="Old Co", api_key="old-key", is_active=True)
    db.add(company)
    db.flush()

    old_time = datetime.utcnow() - timedelta(hours=2)
    payment = Payment(
        company_id=company.id,
        amount=100,
        currency="AED",
        raw_message="Old SMS",
        status="new",
        txn_id="OLD123",
    )
    # set created_at to old timestamp
    payment.created_at = old_time
    db.add(payment)
    db.commit()
    pid = payment.id
    db.close()

    # check with max_age_minutes=10 -> should not be found
    resp = client.post(
        "/payments/check",
        headers={"X-API-Key": "old-key"},
        json={"order_id": "ORD-OLD", "expected_amount": 100, "txn_id": "OLD123", "max_age_minutes": 10},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is False
    assert data["match"] is False
