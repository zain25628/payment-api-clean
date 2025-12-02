from typing import Optional
import os
import json
import logging
import urllib.request
import urllib.error

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.channel import Channel
from app.models.wallet import Wallet
from app.models.payment import Payment
from app.schemas.incoming_sms import IncomingSmsCreate

logger = logging.getLogger(__name__)


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

        # Ensure receiver_phone is not NULL at DB level: fall back to payer_phone
        # Some DB migrations enforce NOT NULL for receiver_phone; use payer_phone
        # as a sensible default when receiver is absent in payload.
        receiver_phone = data.receiver_phone if getattr(data, "receiver_phone", None) is not None else getattr(data, "payer_phone", None)

        # 4) Create Payment
        payment = Payment(
            company_id=company.id,
            channel_id=channel.id,
            wallet_id=wallet.id if wallet is not None else None,
            amount=amount,
            currency=currency,
            txn_id=data.txn_id,
            payer_phone=data.payer_phone,
            receiver_phone=receiver_phone,
            raw_message=data.raw_message,
            # status: "new" will be defaulted by model (__init__ / Column default)
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        # 5) Send Telegram notification (best-effort, non-blocking)
        notify_telegram_about_payment(payment, channel)
        
        return payment


def notify_telegram_about_payment(payment, channel) -> None:
    """Send a Telegram message (best-effort) when a new payment is stored."""
    try:
        # 1) احصل على التوكن:
        company = channel.company if hasattr(channel, "company") else None
        bot_token = None

        # أولوية: company.telegram_bot_token ثم ENV ثم لا شيء
        if company and getattr(company, "telegram_bot_token", None):
            bot_token = company.telegram_bot_token
        elif os.getenv("TELEGRAM_BOT_TOKEN"):
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

        if not bot_token:
            logger.info("Telegram notification skipped: no bot token configured.")
            return

        # 2) احصل على chat_id (group id)
        chat_id = None
        if getattr(channel, "telegram_group_id", None):
            chat_id = channel.telegram_group_id
        elif company and getattr(company, "telegram_default_group_id", None):
            chat_id = company.telegram_default_group_id

        if not chat_id:
            logger.info("Telegram notification skipped: no telegram group id configured.")
            return

        # 3) ابنِ نص الرسالة
        # استخدم getattr بحذر لعدم كسر الكود لو تغيّرت أسماء الحقول
        amount = getattr(payment, "amount", None)
        currency = getattr(payment, "currency", None)
        txn_id = getattr(payment, "txn_id", None)
        payer_phone = getattr(payment, "payer_phone", None)
        receiver_phone = getattr(payment, "receiver_phone", None)
        channel_name = getattr(channel, "name", None) or getattr(channel, "code", None) or "channel"

        lines = [
            "📩 Payment received via SMS",
            f"Channel: {channel_name}",
        ]
        if amount is not None:
            lines.append(f"Amount: {amount} {currency or ''}".strip())
        if txn_id:
            lines.append(f"Txn ID: {txn_id}")
        if payer_phone:
            lines.append(f"Payer: {payer_phone}")
        if receiver_phone:
            lines.append(f"Receiver: {receiver_phone}")

        text = "\n".join(lines)

        # 4) حضّر طلب Telegram sendMessage
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": "HTML",
        }
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=5) as resp:
            # لا نحتاج نستخدم الرد، فقط نسجل نجاح بسيط
            logger.info("Telegram notification sent: status=%s", resp.status)
    except urllib.error.HTTPError as e:
        logger.warning("Telegram notification HTTPError: %s %s", e.code, e.reason)
    except Exception as e:
        logger.warning("Telegram notification failed: %r", e)

