from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.models.country import PaymentProvider
from app.routers.admin_companies import router as admin_companies_router


def create_test_app_and_db():
    # Use a StaticPool + check_same_thread=False so the in-memory SQLite
    # database is shared across threads/connections used by TestClient.
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    app = FastAPI()
    app.include_router(admin_companies_router)

    # Ensure models are imported and registered on Base before creating tables
    # Import model modules so their Table objects are attached to Base.metadata
    import importlib
    importlib.import_module("app.models.company")
    importlib.import_module("app.models.channel")
    importlib.import_module("app.models.country")

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    return app, TestingSessionLocal


def test_create_company_endpoint_creates_company_and_channels():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    provider1 = PaymentProvider(code="eand_money", name="e& money")
    provider2 = PaymentProvider(code="wallet_x", name="Wallet X")
    db.add_all([provider1, provider2])
    db.commit()
    db.close()

    response = client.post(
        "/admin/companies",
        json={
            "name": "Test Co",
            "country_code": "UAE",
            "provider_codes": ["eand_money", "wallet_x"],
            "telegram_bot_token": "123:ABC",
            "telegram_default_group_id": "-1001234567890",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert "api_key" in body
    assert "channels" in body
    assert len(body["channels"]) == 2


def test_list_companies_returns_created_company():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    provider1 = PaymentProvider(code="eand_money", name="e& money")
    db.add(provider1)
    db.commit()
    db.close()

    # create one company
    response = client.post(
        "/admin/companies",
        json={
            "name": "Test Co",
            "country_code": "UAE",
            "provider_codes": ["eand_money"],
        },
    )
    assert response.status_code == 201

    response = client.get("/admin/companies")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert "id" in body[0]
    assert "name" in body[0]
    assert "country_code" in body[0]
    assert "is_active" in body[0]


def test_get_company_returns_404_for_unknown_id():
    app, _ = create_test_app_and_db()
    client = TestClient(app)

    response = client.get("/admin/companies/9999")
    assert response.status_code == 404
    assert response.json().get("detail") == "Company not found"


def test_update_company_endpoint_updates_fields_and_channels():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    provider1 = PaymentProvider(code="eand_money", name="e& money")
    provider2 = PaymentProvider(code="wallet_x", name="Wallet X")
    db.add_all([provider1, provider2])
    db.commit()
    db.close()

    # create initial company
    create_resp = client.post(
        "/admin/companies",
        json={
            "name": "Initial Co",
            "country_code": "UAE",
            "provider_codes": ["eand_money"],
            "telegram_bot_token": None,
            "telegram_default_group_id": None,
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    company_id = created["id"]

    # update to use wallet_x
    update_resp = client.put(
        f"/admin/companies/{company_id}",
        json={
            "name": "Updated Co",
            "country_code": "KSA",
            "provider_codes": ["wallet_x"],
            "telegram_bot_token": "123:ABC",
            "telegram_default_group_id": "-100123",
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()

    assert updated["name"] == "Updated Co"
    assert updated["country_code"] == "KSA"
    assert updated["telegram_bot_token"] == "123:ABC"
    assert len(updated["channels"]) >= 1

    wallet_chs = [c for c in updated["channels"] if c.get("provider_code") == "wallet_x"]
    assert len(wallet_chs) >= 1
    assert any(c.get("is_active") for c in wallet_chs)

    eand_chs = [c for c in updated["channels"] if c.get("provider_code") == "eand_money"]
    if eand_chs:
        assert all(c.get("is_active") is False for c in eand_chs)


def test_update_company_endpoint_returns_404_for_unknown_id():
    app, _ = create_test_app_and_db()
    client = TestClient(app)

    resp = client.put(
        "/admin/companies/9999",
        json={
            "name": "Does Not Exist",
            "country_code": "UAE",
            "provider_codes": [],
        },
    )

    assert resp.status_code == 404
    assert resp.json().get("detail") == "Company not found"


def test_toggle_company_active_flips_flag_via_endpoint():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    provider1 = PaymentProvider(code="eand_money", name="e& money")
    db.add(provider1)
    db.commit()
    db.close()

    create_resp = client.post(
        "/admin/companies",
        json={
            "name": "Toggle Co",
            "country_code": "UAE",
            "provider_codes": ["eand_money"],
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    company_id = created["id"]
    initial_active = created.get("is_active")

    toggle_resp = client.post(f"/admin/companies/{company_id}/toggle")
    assert toggle_resp.status_code == 200
    toggled = toggle_resp.json()
    assert toggled.get("id") == company_id
    assert toggled.get("is_active") != initial_active
