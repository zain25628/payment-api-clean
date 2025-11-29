"""Create a test Payment in the local dev database.

This helper is for local development only. It uses the project's SQLAlchemy
SessionLocal and models to insert a Payment that the merchant demo can match
against when using the seeded `dev-channel-key`.

Usage (from project root):
    & .\.venv\Scripts\Activate.ps1
    python .\create_test_payment.py
"""

from datetime import datetime
import sys

from app.db.session import SessionLocal

# Import models
from app.models.company import Company
from app.models.channel import Channel
from app.models.wallet import Wallet
from app.models.payment import Payment


def main() -> None:
    db = SessionLocal()
    try:
        # Find seeded dev company / channel / wallet
        company = (
            db.query(Company)
            .filter((Company.api_key == "dev-api-key") | (Company.name == "Dev Co"))
            .first()
        )

        if not company:
            print("Dev company not found. Run dev_seed.py first.")
            sys.exit(2)

        channel = db.query(Channel).filter(Channel.channel_api_key == "dev-channel-key").first()
        if not channel:
            print("Dev channel not found. Run dev_seed.py first.")
            sys.exit(2)

        wallet = db.query(Wallet).filter(Wallet.wallet_identifier == "WALLET-DEV-001").first()
        if not wallet:
            print("Dev wallet not found. Run dev_seed.py first.")
            sys.exit(2)

        # Create a Payment that will match expected_amount=10 in the merchant demo
        payment = Payment(
            company_id=company.id,
            channel_id=channel.id,
            wallet_id=wallet.id,
            amount=10,
            currency="AED",
            txn_id="TEST-TXN-001",
            payer_phone="0500000000",
            receiver_phone=wallet.wallet_identifier,
            raw_message="Test payment 10 AED",
            status="new",
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        print("Created test payment:")
        print(f"  id: {payment.id}")
        print(f"  txn_id: {payment.txn_id}")
        print(f"  amount: {payment.amount} {payment.currency}")
        print(f"  order_id: {payment.order_id}")
        print(f"  confirm_token: {payment.confirm_token}")
        print(f"  created_at: {payment.created_at}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
