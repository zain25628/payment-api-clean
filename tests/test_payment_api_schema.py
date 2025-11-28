from datetime import datetime

from app.schemas.payment_api import (
    PaymentCheckRequest,
    PaymentMatchInfo,
    PaymentCheckResponse,
    PaymentConfirmRequest,
    PaymentConfirmResponse,
)


def test_payment_check_request_basic_fields():
    req = PaymentCheckRequest(order_id="ORD-1", expected_amount=150)
    assert req.order_id == "ORD-1"
    assert req.expected_amount == 150
    assert req.max_age_minutes == 30


def test_payment_check_response_match_payload():
    now = datetime.utcnow()
    match = PaymentMatchInfo(payment_id=1, txn_id="TXN123", amount=150, currency="AED", created_at=now)
    resp = PaymentCheckResponse(found=True, match=True, confirm_token="tok-1", order_id="ORD-1", payment=match)

    assert resp.found is True
    assert resp.match is True
    assert resp.confirm_token == "tok-1"
    assert resp.payment is not None
    assert resp.payment.payment_id == 1
    assert resp.payment.created_at == now


def test_payment_check_response_mismatch_reason():
    now = datetime.utcnow()
    match = PaymentMatchInfo(payment_id=2, txn_id=None, amount=200, currency="AED", created_at=now)
    resp = PaymentCheckResponse(found=True, match=False, reason="amount_mismatch", payment=match)

    assert resp.found is True
    assert resp.match is False
    assert resp.reason == "amount_mismatch"
    assert resp.payment.amount == 200


def test_payment_confirm_request_and_response_basic():
    req = PaymentConfirmRequest(payment_id=5, confirm_token="token-xyz")
    assert req.payment_id == 5
    assert req.confirm_token == "token-xyz"

    resp = PaymentConfirmResponse(success=True, already_used=False, payment_id=5, status="used")
    assert resp.success is True
    assert resp.already_used is False
    assert resp.payment_id == 5
    assert resp.status == "used"
