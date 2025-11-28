from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.models.company import Company
from app.models.payment import Payment
from app.routers.payments import router as payments_router


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
    importlib.import_module("app.models.payment")
    # also import related models to avoid NoReferencedTableError
    importlib.import_module("app.models.channel")
    importlib.import_module("app.models.wallet")
    importlib.import_module("app.models.country")

    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(payments_router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    return app, TestingSessionLocal


def test_payments_check_endpoint_match_flow():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    company = Company(name="Test Co", api_key="company-key", is_active=True)
    db.add(company)
    db.flush()

    payment = Payment(
        company_id=company.id,
        amount=150,
        currency="AED",
        raw_message="Test SMS",
        status="new",
    )
    db.add(payment)
    db.commit()
    payment_id = payment.id
    db.close()

    resp = client.post(
        "/payments/check",
        headers={"X-API-Key": "company-key"},
        json={
            "order_id": "ORD-1",
            "expected_amount": 150,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is True
    assert data["match"] is True
    assert data["confirm_token"] is not None
    assert data["payment"]["payment_id"] == payment_id


def test_payments_check_endpoint_mismatch_flow():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    company = Company(name="Test Co", api_key="company-key", is_active=True)
    db.add(company)
    db.flush()

    payment = Payment(
        company_id=company.id,
        amount=200,
        currency="AED",
        raw_message="Test SMS",
        status="new",
    )
    db.add(payment)
    db.commit()
    payment_id = payment.id
    db.close()

    resp = client.post(
        "/payments/check",
        headers={"X-API-Key": "company-key"},
        json={
            "order_id": "ORD-2",
            "expected_amount": 150,
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is True
    assert data["match"] is False
    assert data["reason"] == "amount_mismatch"


def test_payments_confirm_endpoint_happy_path_and_idempotent():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    company = Company(name="Test Co", api_key="company-key", is_active=True)
    db.add(company)
    db.flush()

    payment = Payment(
        company_id=company.id,
        amount=150,
        currency="AED",
        raw_message="Test SMS",
        status="new",
    )
    db.add(payment)
    db.commit()
    payment_id = payment.id
    db.close()

    # أولاً: نعمل check للحصول على confirm_token
    check_resp = client.post(
        "/payments/check",
        headers={"X-API-Key": "company-key"},
        json={
            "order_id": "ORD-1",
            "expected_amount": 150,
        },
    )
    assert check_resp.status_code == 200
    check_data = check_resp.json()
    token = check_data["confirm_token"]

    # ثم: نستدعي confirm لأول مرة
    confirm_resp1 = client.post(
        "/payments/confirm",
        headers={"X-API-Key": "company-key"},
        json={
            "payment_id": payment_id,
            "confirm_token": token,
        },
    )
    assert confirm_resp1.status_code == 200
    body1 = confirm_resp1.json()
    assert body1["success"] is True
    assert body1["already_used"] is False
    assert body1["status"] == "used"

    # ثاني مرة (idempotent)
    confirm_resp2 = client.post(
        "/payments/confirm",
        headers={"X-API-Key": "company-key"},
        json={
            "payment_id": payment_id,
            "confirm_token": token,
        },
    )
    assert confirm_resp2.status_code == 200
    body2 = confirm_resp2.json()
    assert body2["success"] is True
    assert body2["already_used"] is True
    assert body2["status"] == "used"


def test_payments_confirm_endpoint_invalid_token_returns_400():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    company = Company(name="Test Co", api_key="company-key", is_active=True)
    db.add(company)
    db.flush()

    payment = Payment(
        company_id=company.id,
        amount=150,
        currency="AED",
        raw_message="Test SMS",
        status="new",
    )
    db.add(payment)
    db.commit()
    payment_id = payment.id
    db.close()

    resp = client.post(
        "/payments/confirm",
        headers={"X-API-Key": "company-key"},
        json={
            "payment_id": payment_id,
            "confirm_token": "wrong-token",
        },
    )

    assert resp.status_code == 400
    body = resp.json()
    assert body.get("detail") == "Invalid payment_id or confirm_token"
