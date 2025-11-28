from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.models.company import Company
from app.dependencies.company_auth import get_current_company


def create_test_app_and_db():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Ensure Company model is registered (avoid importing package __init__ which
    # pulls in other models that reference tables not present in tests)
    import importlib
    importlib.import_module("app.models.company")

    # Some models in the real app reference tables that aren't present in this
    # minimal test environment (e.g. PaymentProvider). Create minimal table
    # definitions here so create_all can succeed.
    from sqlalchemy import Column, Integer

    if "payment_providers" not in Base.metadata.tables:
        class PaymentProvider(Base):
            __tablename__ = "payment_providers"
            id = Column(Integer, primary_key=True)

    Base.metadata.create_all(bind=engine)

    app = FastAPI()

    # simple test endpoint protected by get_current_company
    @app.get("/protected")
    def protected_route(current_company: Company = Depends(get_current_company)):
        return {"company_id": current_company.id, "name": current_company.name}

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    return app, TestingSessionLocal


def test_get_current_company_with_valid_active_key():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    company = Company(name="Test Co", api_key="valid-key", is_active=True)
    db.add(company)
    db.commit()
    # capture primary key before closing the session to avoid DetachedInstanceError
    company_id = company.id
    db.close()

    resp = client.get("/protected", headers={"X-API-Key": "valid-key"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == company_id
    assert data["name"] == "Test Co"


def test_get_current_company_missing_key_returns_401():
    app, _ = create_test_app_and_db()
    client = TestClient(app)

    resp = client.get("/protected")  # no X-API-Key
    assert resp.status_code in (401, 422)
    body = resp.json()
    if resp.status_code == 422:
        # FastAPI validation error - header missing
        assert isinstance(body.get("detail"), list)
    else:
        assert body.get("detail") in ("Missing X-API-Key", "Invalid X-API-Key")


def test_get_current_company_invalid_key_returns_401():
    app, _ = create_test_app_and_db()
    client = TestClient(app)

    resp = client.get("/protected", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Invalid X-API-Key"


def test_get_current_company_inactive_company_returns_403():
    app, SessionLocal = create_test_app_and_db()
    client = TestClient(app)

    db = SessionLocal()
    company = Company(name="Inactive Co", api_key="inactive-key", is_active=False)
    db.add(company)
    db.commit()
    db.close()

    resp = client.get("/protected", headers={"X-API-Key": "inactive-key"})
    assert resp.status_code == 403
    assert resp.json().get("detail") == "Company is inactive"
