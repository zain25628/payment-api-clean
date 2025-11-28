from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.routers.admin_payment_providers import router as admin_payment_providers_router


def create_test_app_and_db():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # ensure models are registered
    import importlib
    importlib.import_module("app.models.country")

    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(admin_payment_providers_router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    return app, TestingSessionLocal


def test_list_payment_providers_endpoint_returns_providers():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    from app.models.country import PaymentProvider

    p1 = PaymentProvider(code="eand_money", name="e& money")
    p2 = PaymentProvider(code="wallet_x", name="Wallet X")
    db.add_all([p1, p2])
    db.commit()
    db.close()

    resp = client.get("/admin/payment-providers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    codes = {p["code"] for p in data}
    assert "eand_money" in codes and "wallet_x" in codes


def test_create_payment_provider_creates_provider_and_links_country():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    from app.models.country import Country, CountryPaymentProvider

    country = Country(code="UAE", name="United Arab Emirates")
    db.add(country)
    db.commit()

    resp = client.post(
        "/admin/payment-providers",
        json={"code": "eand_money", "name": "e& money", "country_code": "UAE"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body.get("code") == "eand_money"

    # ensure a linking row was created
    link = db.query(CountryPaymentProvider).join(Country, Country.id == CountryPaymentProvider.country_id).filter(Country.code == "UAE").first()
    assert link is not None
    assert link.is_supported is True
    db.close()
