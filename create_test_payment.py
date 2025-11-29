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
import argparse

from app.db.session import SessionLocal

# Import models
from app.models.company import Company
from app.models.channel import Channel
from app.models.wallet import Wallet
from app.models.payment import Payment


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a dev test payment for the seeded Dev Co/channel/wallet."
    )
    parser.add_argument("--amount", type=int, default=10, help="Payment amount (default: 10)")
    parser.add_argument(
        "--txn-id",
        dest="txn_id",
        type=str,
        default="TEST-TXN-001",
        help="External transaction ID (default: TEST-TXN-001)",
    )
    parser.add_argument(
        "--payer-phone",
        dest="payer_phone",
        type=str,
        default="+971500000000",
        help="Payer phone number (default: +971500000000)",
    )

    args = parser.parse_args()

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

        # Ensure txn_id uniqueness: if an existing payment uses the same txn_id,
        # avoid IntegrityError by creating a slightly-modified txn_id.
        existing = db.query(Payment).filter(Payment.txn_id == args.txn_id).first()
        txn_to_use = args.txn_id
        if existing is not None:
            suffix = int(datetime.utcnow().timestamp())
            txn_to_use = f"{args.txn_id}-{suffix}"
            print(f"Warning: txn_id '{args.txn_id}' already exists; using '{txn_to_use}' instead")

        # Create a Payment that will match expected_amount in the merchant demo
        payment = Payment(
            company_id=company.id,
            channel_id=channel.id,
            wallet_id=wallet.id,
            amount=args.amount,
            currency="AED",
            txn_id=txn_to_use,
            payer_phone=args.payer_phone,
            receiver_phone=wallet.wallet_identifier,
            raw_message=f"Test payment {args.amount} AED",
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
