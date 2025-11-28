from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.company import Company
from app.models.payment import Payment
from app.schemas.payment_api import (
    PaymentCheckRequest,
    PaymentConfirmRequest,
)
from app.services.payment_service import PaymentService


def create_test_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Ensure models are registered
    import importlib
    importlib.import_module("app.models.company")
    importlib.import_module("app.models.payment")

    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_check_payment_match_sets_pending_and_token():
    db = create_test_session()
    try:
        company = Company(name="Test Co", api_key="test-key")
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

        req = PaymentCheckRequest(order_id="ORD-1", expected_amount=150)
        resp = PaymentService.check_payment_for_company(db, company_id=company.id, req=req)

        assert resp.found is True
        assert resp.match is True
        assert resp.confirm_token is not None
        assert resp.payment is not None
        assert resp.payment.payment_id == payment.id

        db.refresh(payment)
        assert payment.status == "pending_confirmation"
        assert payment.order_id == "ORD-1"
        assert payment.confirm_token == resp.confirm_token
    finally:
        db.close()


def test_check_payment_mismatch_does_not_change_status():
    db = create_test_session()
    try:
        company = Company(name="Test Co", api_key="test-key")
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

        req = PaymentCheckRequest(order_id="ORD-2", expected_amount=150)
        resp = PaymentService.check_payment_for_company(db, company_id=company.id, req=req)

        assert resp.found is True
        assert resp.match is False
        assert resp.reason == "amount_mismatch"
        db.refresh(payment)
        assert payment.status == "new"
        assert payment.confirm_token is None
    finally:
        db.close()


def test_check_payment_not_found_returns_false():
    db = create_test_session()
    try:
        company = Company(name="Test Co", api_key="test-key")
        db.add(company)
        db.commit()

        req = PaymentCheckRequest(order_id="ORD-3", expected_amount=50)
        resp = PaymentService.check_payment_for_company(db, company_id=company.id, req=req)

        assert resp.found is False
        assert resp.match is False
    finally:
        db.close()


def test_confirm_payment_happy_path_and_idempotent():
    db = create_test_session()
    try:
        company = Company(name="Test Co", api_key="test-key")
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

        # run check to set pending + token
        check_req = PaymentCheckRequest(order_id="ORD-1", expected_amount=150)
        check_resp = PaymentService.check_payment_for_company(db, company.id, check_req)
        token = check_resp.confirm_token
        payment_id = check_resp.payment.payment_id

        confirm_req = PaymentConfirmRequest(payment_id=payment_id, confirm_token=token)
        confirm_resp1 = PaymentService.confirm_payment_for_company(db, company.id, confirm_req)

        assert confirm_resp1.success is True
        assert confirm_resp1.already_used is False
        assert confirm_resp1.status == "used"

        # second time (idempotent)
        confirm_resp2 = PaymentService.confirm_payment_for_company(db, company.id, confirm_req)
        assert confirm_resp2.success is True
        assert confirm_resp2.already_used is True
        assert confirm_resp2.status == "used"

        # ensure DB updated
        db.refresh(payment)
        assert payment.status == "used"
        assert payment.used_at is not None
    finally:
        db.close()


def test_confirm_payment_invalid_token_raises():
    db = create_test_session()
    try:
        company = Company(name="Test Co", api_key="test-key")
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

        with pytest.raises(ValueError):
            PaymentService.confirm_payment_for_company(
                db,
                company_id=company.id,
                req=PaymentConfirmRequest(payment_id=payment.id, confirm_token="wrong"),
            )
    finally:
        db.close()
import types
import pytest
from datetime import datetime, timezone

import app.services.payment_service as payment_service
from app.models.payment import Payment


class _FakeSession:
    """Minimal fake session for testing persistence helpers.

    This fake session stores added objects in a list and provides no real
    query/filter capabilities. It is intentionally minimal for unit tests
    that do not exercise SQLAlchemy behavior.
    """

    def __init__(self):
        self._store = []

    def add(self, obj):
        # mimic SQLAlchemy: adding registers the object
        if obj not in self._store:
            self._store.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        # no-op: object is already mutable in-place
        return obj

    # Minimal `query` used in one test to simulate "no results" behavior
    def query(self, model):
        class _EmptyQuery:
            def filter(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def first(self):
                return None

        return _EmptyQuery()


def test_create_payment_from_sms_basic():
    db = _FakeSession()
    payload = {
        "company_id": 1,
        "channel_id": 2,
        "amount": 123.45,
        "payer_phone": "+10000000000",
        "receiver_phone": "+19999999999",
        "raw_message": "PAY 123.45",
        "currency": "USD",
    }

    payment = payment_service.create_payment_from_sms(db, payload)

    assert isinstance(payment, Payment)
    assert payment.company_id == payload["company_id"]
    assert payment.channel_id == payload["channel_id"]
    assert payment.amount == payload["amount"]
    assert payment.payer_phone == payload["payer_phone"]
    assert payment.receiver_phone == payload["receiver_phone"]


def test_confirm_payment_usage_updates_status_and_used_at(monkeypatch):
    db = _FakeSession()

    # create a Payment-like object (SQLAlchemy model instance)
    payment = Payment()
    payment.id = 999
    payment.wallet_id = 42
    payment.amount = 50.0
    payment.status = "pending_confirmation"
    payment.used_at = None

    called = {}

    def fake_update_wallet_usage(db_arg, wallet_id, amount):
        called["wallet_id"] = wallet_id
        called["amount"] = amount

    # Monkeypatch the update_wallet_usage used by the payment_service module
    monkeypatch.setattr(payment_service, "update_wallet_usage", fake_update_wallet_usage)

    ret = payment_service.confirm_payment_usage(db, payment)

    assert ret is payment
    assert payment.status == "used"
    assert payment.used_at is not None
    # used_at must be timezone-aware and set to UTC
    assert payment.used_at.tzinfo is not None
    assert payment.used_at.tzinfo == timezone.utc
    assert called.get("wallet_id") == 42
    assert called.get("amount") == 50.0


def test_match_payment_for_order_no_match_returns_none():
    db = _FakeSession()
    result = payment_service.match_payment_for_order(db, company_id=1, amount=10.0, currency="USD")
    assert result is None
