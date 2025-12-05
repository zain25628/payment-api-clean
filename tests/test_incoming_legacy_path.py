from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.models.company import Company
from app.models.channel import Channel
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
    importlib.import_module("app.models.payment")
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


def test_legacy_header_only_creates_payment_and_falls_back_receiver():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    company = Company(name="Legacy Co", api_key="legacy-key")
    db.add(company)
    db.flush()

    channel = Channel(
        company_id=company.id,
        name="Legacy Channel",
        channel_api_key="legacy-chan-123",
    )
    db.add(channel)
    db.commit()
    db.close()

    # Legacy flow: no channel_api_key in body, but X-API-Key header is provided
    resp = client.post(
        "/incoming-sms/",
        headers={"X-API-Key": "legacy-key"},
        json={
            "payer_phone": "+971500000002",
            "raw_message": "legacy test",
        },
    )

    assert resp.status_code in (200, 201)
    body = resp.json()
    assert "payment_id" in body

    db2 = SessionLocal()
    payment = db2.query(Payment).filter(Payment.id == body["payment_id"]).first()
    assert payment is not None
    # receiver_phone should have fallen back to payer_phone
    assert payment.receiver_phone == "+971500000002"
    assert payment.status == "new"
    db2.close()
