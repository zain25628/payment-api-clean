
# Refactored by Copilot – SMS Service Feature
"""SMS parsing and persistence helpers.

This module validates channel API keys, parses incoming SMS payloads into a
normalized mapping ready for persistence, and stores payments by delegating
to `payment_service.create_payment_from_sms`.
"""
from typing import Optional, Dict
import logging
from sqlalchemy.orm import Session
from app.models.channel import Channel
from app.models.payment import Payment
from app.models.wallet import Wallet
from app.services.payment_service import create_payment_from_sms
 
logger = logging.getLogger("payment_gateway")


def classify_sms(raw: str) -> str:
    """Classify incoming SMS text as 'deposit' or 'ignored'.

    Rules (case-insensitive):
    - If message contains "good news" AND "aed" AND ("landed" OR "from")
      then it's a deposit.
    - Otherwise it's ignored.

    Returns:
        "deposit" or "ignored"
    """
    if not raw:
        return "ignored"
    low = raw.lower()
    if ("good news" in low) and ("aed" in low) and (("landed" in low) or ("from" in low)):
        return "deposit"
    return "ignored"


def validate_channel_api_key(db: Session, api_key: str) -> Optional[Channel]:
    """Return the active Channel matching `api_key` or None.

    Args:
        db: SQLAlchemy Session.
        api_key: The channel API key header value.
    """
    if not api_key:
        return None

    key = api_key.strip()
    return (
        db.query(Channel)
        .filter(
            Channel.channel_api_key == key,
            Channel.is_active == True,  # noqa: E712
        )
        .first()
    )


def parse_incoming_sms(payload: Dict) -> Dict:
    """Normalize raw incoming SMS payload into fields used for Payment creation.

    Expects (optionally): `payer_phone`, `receiver_phone`, `raw_message`,
    `amount`, `currency`, `txn_id`.

    Returns a dict with keys: `payer_phone`, `receiver_phone`, `raw_message`,
    `amount` (float), `currency` (default 'USD'), `txn_id`.
    """
    # Ensure receiver_phone falls back to payer_phone when absent to
    # avoid NOT NULL DB constraint issues in legacy flows.
    payer = payload.get("payer_phone")
    receiver = payload.get("receiver_phone") or payer

    raw_message = str(payload.get("raw_message") or "").strip()

    # Safely parse explicit amount: if malformed, leave as None to try extraction
    raw_amount = payload.get("amount", None)
    amount = None
    try:
        if raw_amount is not None and raw_amount != "":
            amount = float(raw_amount)
    except (ValueError, TypeError):
        amount = None

    currency = payload.get("currency")
    txn_id = payload.get("txn_id")

    # Local-only parsed metadata (do NOT include these in the returned dict)
    direction = None
    balance_after = None
    parsed_txn_local = None

    # Try to parse both incoming and outgoing e& money formats
    try:
        import re

        pat_currency_amount = re.compile(r"\b(AED|USD|SAR|OMR)\b\s*([0-9]+(?:\.[0-9]+)?)", flags=re.I)
        pat_balance = re.compile(r"(?i)(?:New balance:|Check your new balance:)\s*([0-9]+(?:\.[0-9]+)?)")
        pat_txn = re.compile(r"(?i)Transaction ID:\s*(\d+)")

        # Direction detection
        if re.search(r"(?i)(landed in your account|Good news!)", raw_message):
            direction = "incoming"
        elif re.search(r"(?i)^You sent\b|(?i)You sent\s", raw_message):
            direction = "outgoing"

        # Amount & currency extraction (override only when missing/invalid)
        if (amount is None) or (amount == 0.0) or (not currency):
            m_amt = pat_currency_amount.search(raw_message)
            if m_amt:
                raw_amt = m_amt.group(2).replace(",", ".")
                try:
                    parsed_amount = float(raw_amt)
                except (ValueError, TypeError):
                    parsed_amount = None
                if parsed_amount is not None and ((amount is None) or (amount == 0.0)):
                    amount = parsed_amount
                if not currency:
                    currency = m_amt.group(1).upper()

        # Balance after
        b = pat_balance.search(raw_message)
        if b:
            try:
                balance_after = float(b.group(1).replace(",", "."))
            except (ValueError, TypeError):
                balance_after = None

        # Transaction id
        t = pat_txn.search(raw_message)
        if t:
            parsed_txn_local = t.group(1)
            # Keep txn_id in returned dict as before, but do not expose other extra fields
            if not txn_id:
                txn_id = parsed_txn_local

        # debug log (avoid printing raw_message again)
        logger = logging.getLogger("payment_gateway")
        logger.debug("parse_incoming_sms: direction=%s amount=%s currency=%s txn=%s balance_after=%s", direction, amount, currency, parsed_txn_local, balance_after)
    except Exception:
        # parsing should be best-effort and never raise
        direction = None
        balance_after = None
        parsed_txn_local = None

    # Try intelligent extraction from raw_message when amount or currency missing
    logger = logging.getLogger("payment_gateway")
    if (amount is None) or (not currency):
        import re

        # Use the specific currency/amount pattern requested (case-insensitive)
        pat_currency_amount = re.compile(r"(?i)\b(AED|USD|SAR|OMR)\b\s*([0-9]+(?:\.[0-9]+)?)")
        pat_txn = re.compile(r"(?i)(?:Transaction ID|Txn ID|Txn|Transaction #:?)[:\s]*([A-Za-z0-9-]+)")
        pat_balance = re.compile(r"(?i)Check your new balance[:\s]*([0-9]+(?:\.[0-9]+)?)")

        m = pat_currency_amount.search(raw_message)

        if m and (amount is None):
            raw_amt = m.group(2)
            try:
                amount = float(raw_amt)
            except (ValueError, TypeError):
                amount = None

        if m and (not currency):
            currency = m.group(1).upper()

        # extract txn id and balance if present
        if not txn_id:
            t = pat_txn.search(raw_message)
            if t:
                txn_id = t.group(1)

        balance = None
        b = pat_balance.search(raw_message)
        if b:
            try:
                balance = float(b.group(1))
            except (ValueError, TypeError):
                balance = None

        payer_name = None
        # optional: try to capture payer name from 'from <NAME>' patterns
        try:
            pat_from = re.compile(r"(?i)from\s+([A-Z0-9][A-Za-z0-9 \-']{1,80}?)")
            f = pat_from.search(raw_message)
            if f:
                payer_name = f.group(1).strip()
        except Exception:
            payer_name = None

        logger.debug("parse_incoming_sms: extracted amount=%s currency=%s txn_id=%s balance=%s", amount, currency, txn_id, balance)

    # final fallbacks
    if amount is None:
        amount = 0.0
    if not currency:
        currency = payload.get("currency", "USD")

    result = {
        "payer_phone": payer,
        "receiver_phone": receiver,
        "raw_message": raw_message,
        "amount": float(amount),
        "currency": currency,
        "txn_id": txn_id,
    }

    # Note: we intentionally do NOT attach extra parsed fields (payer_name,
    # balance_after, direction, etc.) to the returned dict here. Those are
    # kept as local metadata for future use or logging only so that the
    # `payment_data` passed to `Payment(**...)` contains only recognized
    # model fields.

    return result


def store_payment(db: Session, channel_id: int, company_id: int, parsed_data: Dict) -> Payment:
    """Persist a Payment built from `parsed_data` and return the created Payment.

    This function augments `parsed_data` with `channel_id`, `company_id`, and
    a default `status` of `new`, then delegates to
    `payment_service.create_payment_from_sms`.
    """
    # Classify the SMS first: ignore non-deposit messages without inserting into DB
    raw_message = parsed_data.get("raw_message")
    classification = classify_sms(str(raw_message or ""))
    if classification != "deposit":
        logger.info("store_payment ignored (not a deposit): %s", raw_message)
        return {"status": "ignored - not a deposit"}

    # Attempt to map receiver_phone to a Wallet for this company (legacy path)
    receiver_phone = parsed_data.get("receiver_phone")

    wallet_id = None
    if receiver_phone:
        try:
            wallet = (
                db.query(Wallet)
                .filter(
                    Wallet.company_id == company_id,
                    Wallet.wallet_identifier == receiver_phone,
                    Wallet.is_active == True,
                )
                .first()
            )
            if wallet:
                wallet_id = wallet.id
        except Exception:
            # Best-effort lookup: do not fail the flow if DB lookup errors
            logger.exception("store_payment: wallet lookup failed for receiver_phone=%s", receiver_phone)

    if wallet_id is not None:
        logger.info(
            "store_payment: mapped receiver_phone %s to wallet_id=%s",
            receiver_phone,
            wallet_id,
        )

    payment_data = parsed_data.copy()
    payment_data["channel_id"] = channel_id
    payment_data["company_id"] = company_id
    payment_data["status"] = "new"
    if wallet_id is not None:
        payment_data["wallet_id"] = wallet_id

    return create_payment_from_sms(db, payment_data)
