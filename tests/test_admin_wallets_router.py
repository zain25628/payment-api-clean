from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.models.country import PaymentProvider
from app.routers.admin_wallets import router as admin_wallets_router
from app.models.company import Company
from app.models.channel import Channel


def create_test_app_and_db():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    app = FastAPI()
    app.include_router(admin_wallets_router)

    import importlib
    importlib.import_module("app.models.company")
    importlib.import_module("app.models.channel")
    importlib.import_module("app.models.country")
    importlib.import_module("app.models.wallet")

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return app, TestingSessionLocal


def test_admin_create_and_list_wallets_for_company():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    provider = PaymentProvider(code="wallet_x", name="Wallet X")
    db.add(provider)
    db.commit()

    # create company and channel directly using DB session
    c = Company(name="C1", api_key="k1")
    db.add(c)
    db.commit()

    ch = Channel(company_id=c.id, name="chan1", provider_id=None, channel_api_key="ck1", is_active=True)
    db.add(ch)
    db.commit()

    # create wallet via admin endpoint
    resp = client.post(f"/admin/companies/{c.id}/wallets", json={
        "wallet_label": "W1",
        "wallet_identifier": "1001",
        "daily_limit": 1000,
        "is_active": True,
        "channel_id": ch.id,
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body.get("wallet_label") == "W1"

    # list wallets
    list_resp = client.get(f"/admin/companies/{c.id}/wallets")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(i.get("wallet_identifier") == "1001" for i in items)


def test_admin_update_wallet_and_toggle():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    c = Company(name="C2", api_key="k2")
    db.add(c)
    db.commit()

    ch = Channel(company_id=c.id, name="chan2", provider_id=None, channel_api_key="ck2", is_active=True)
    db.add(ch)
    db.commit()

    # create wallet
    resp = client.post(f"/admin/companies/{c.id}/wallets", json={
        "wallet_label": "W-Up",
        "wallet_identifier": "2001",
        "daily_limit": 500,
        "is_active": True,
        "channel_id": ch.id,
    })
    assert resp.status_code == 201
    w = resp.json()
    wid = w["id"]

    # update
    put_resp = client.put(f"/admin/wallets/{wid}", json={"wallet_label": "W-Updated", "daily_limit": 750})
    assert put_resp.status_code == 200
    updated = put_resp.json()
    assert updated.get("wallet_label") == "W-Updated"
    assert float(updated.get("daily_limit", 0)) == 750.0

    # toggle
    tog = client.post(f"/admin/wallets/{wid}/toggle")
    assert tog.status_code == 200
    toggled = tog.json()
    assert toggled.get("is_active") is False
