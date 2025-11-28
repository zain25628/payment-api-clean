from datetime import datetime

from app.schemas.incoming_sms import (
    IncomingSmsBase,
    IncomingSmsCreate,
    IncomingSmsStored,
)


def test_incoming_sms_base_minimal_payload():
    payload = IncomingSmsBase(
        channel_api_key="chan-key-123",
        raw_message="تم تحويل 150 درهم...",
    )

    assert payload.channel_api_key == "chan-key-123"
    assert payload.raw_message.startswith("تم تحويل")
    assert payload.currency == "AED"
    assert payload.amount is None


def test_incoming_sms_base_full_payload():
    ts = datetime.utcnow()
    payload = IncomingSmsBase(
        channel_api_key="chan-key-123",
        provider="eand_money",
        raw_message="message",
        amount=150,
        currency="AED",
        txn_id="TXN123",
        payer_phone="0500000000",
        receiver_phone="0511111111",
        timestamp=ts,
    )

    assert payload.provider == "eand_money"
    assert payload.amount == 150
    assert payload.txn_id == "TXN123"
    assert payload.payer_phone == "0500000000"
    assert payload.receiver_phone == "0511111111"
    assert payload.timestamp == ts


def test_incoming_sms_create_is_compatible_with_base():
    data = IncomingSmsCreate(
        channel_api_key="chan-key-xyz",
        raw_message="msg",
    )
    assert isinstance(data, IncomingSmsBase)
    assert data.channel_api_key == "chan-key-xyz"


def test_incoming_sms_stored_basic():
    stored = IncomingSmsStored(payment_id=1, status="new")
    assert stored.payment_id == 1
    assert stored.status == "new"
