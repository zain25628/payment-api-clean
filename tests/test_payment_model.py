from app.models.company import Company
from app.models.channel import Channel
from app.models.payment import Payment
from app.models.country import PaymentProvider


def test_payment_basic_fields_assignment():
    company = Company(name="Test Co", api_key="test-key")
    channel = Channel(company_id=1, name="Test Channel", channel_api_key="chan-key")
    payment = Payment(
        company=company,
        channel=channel,
        amount=150,
        currency="AED",
        txn_id="TXN123",
        payer_phone="0500000000",
        receiver_phone="0511111111",
        raw_message="Test payment message",
        status="new",
        order_id="ORD-1",
        confirm_token="token-123",
    )

    assert payment.amount == 150
    assert payment.currency == "AED"
    assert payment.txn_id == "TXN123"
    assert payment.payer_phone == "0500000000"
    assert payment.receiver_phone == "0511111111"
    assert payment.raw_message == "Test payment message"
    assert payment.status == "new"
    assert payment.order_id == "ORD-1"
    assert payment.confirm_token == "token-123"


def test_payment_defaults_and_relationships():
    company = Company(name="Test Co", api_key="test-key")
    channel = Channel(company_id=1, name="Test Channel", channel_api_key="chan-key")
    payment = Payment(
        company=company,
        channel=channel,
        amount=200,
        currency="AED",
        raw_message="Raw SMS",
    )

    assert payment.status == "new"
    assert payment.txn_id is None
    assert payment.payer_phone is None
    assert payment.receiver_phone is None
    assert payment.order_id is None
    assert payment.confirm_token is None

    # relationships should link objects in-memory
    assert payment.company is company
    assert payment.channel is channel
    assert payment in company.payments
    assert payment in channel.payments
