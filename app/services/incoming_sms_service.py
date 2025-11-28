from typing import Optional

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.channel import Channel
from app.models.wallet import Wallet
from app.models.payment import Payment
from app.schemas.incoming_sms import IncomingSmsCreate


class IncomingSmsService:
    @staticmethod
    def store_incoming_sms(db: Session, data: IncomingSmsCreate) -> Payment:
        """
        Resolve the Channel by channel_api_key and store an incoming SMS as a Payment.

        - Finds the Channel by `data.channel_api_key`.
        - Uses the Channel's company as owner for the Payment.
        - Optionally links a Wallet by receiver_phone if available.
        - Creates a Payment with status "new" (default).
        """
        # 1) Find channel by api key
        channel: Optional[Channel] = (
            db.query(Channel)
            .filter(Channel.channel_api_key == data.channel_api_key)
            .first()
        )
        if channel is None:
            # We intentionally raise a ValueError here; the router layer can translate it to HTTP 400/401.
            raise ValueError("Invalid channel_api_key")

        company: Company = channel.company

        # 2) Try to find a wallet by receiver_phone (optional)
        wallet: Optional[Wallet] = None
        if data.receiver_phone:
            wallet = (
                db.query(Wallet)
                .filter(
                    Wallet.company_id == company.id,
                    Wallet.wallet_identifier == data.receiver_phone,
                )
                .first()
            )

        # 3) Prepare amount / currency with safe defaults
        amount = data.amount if data.amount is not None else 0
        currency = data.currency or "AED"

        # 4) Create Payment
        payment = Payment(
            company_id=company.id,
            channel_id=channel.id,
            wallet_id=wallet.id if wallet is not None else None,
            amount=amount,
            currency=currency,
            txn_id=data.txn_id,
            payer_phone=data.payer_phone,
            receiver_phone=data.receiver_phone,
            raw_message=data.raw_message,
            # status: "new" will be defaulted by model (__init__ / Column default)
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment
