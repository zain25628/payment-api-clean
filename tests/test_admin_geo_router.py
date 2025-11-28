from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.models.country import Country, PaymentProvider, CountryPaymentProvider
from app.routers.admin_geo import router as admin_geo_router


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
    app.include_router(admin_geo_router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    return app, TestingSessionLocal


def test_list_countries_endpoint_returns_countries():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    c1 = Country(code="KSA", name="Saudi Arabia")
    c2 = Country(code="UAE", name="United Arab Emirates")
    db.add_all([c1, c2])
    db.commit()
    db.close()

    resp = client.get("/admin/geo/countries")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    codes = {c["code"] for c in data}
    assert "KSA" in codes and "UAE" in codes


def test_list_payment_providers_endpoint_returns_providers():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    p1 = PaymentProvider(code="eand_money", name="e& money")
    p2 = PaymentProvider(code="wallet_x", name="Wallet X")
    db.add_all([p1, p2])
    db.commit()
    db.close()

    resp = client.get("/admin/geo/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    codes = {p["code"] for p in data}
    assert "eand_money" in codes and "wallet_x" in codes


def test_get_country_with_providers_endpoint_returns_supported_only():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    country = Country(code="UAE", name="United Arab Emirates")
    p1 = PaymentProvider(code="eand_money", name="e& money")
    p2 = PaymentProvider(code="wallet_x", name="Wallet X")
    db.add_all([country, p1, p2])
    db.commit()

    link1 = CountryPaymentProvider(country_id=country.id, provider_id=p1.id, is_supported=True)
    link2 = CountryPaymentProvider(country_id=country.id, provider_id=p2.id, is_supported=False)
    db.add_all([link1, link2])
    db.commit()
    db.close()

    resp = client.get("/admin/geo/countries/UAE/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["country"]["code"] == "UAE"
    assert isinstance(data["providers"], list)
    assert len(data["providers"]) == 1
    assert data["providers"][0]["code"] == "eand_money"


def test_get_country_with_providers_endpoint_returns_404_for_unknown_code():
    app, _ = create_test_app_and_db()
    client = TestClient(app)

    resp = client.get("/admin/geo/countries/XXX/providers")
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Country not found"
