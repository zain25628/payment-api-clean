from datetime import datetime, timedelta
import secrets
from typing import Optional

from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.schemas.payment_api import (
    PaymentCheckRequest,
    PaymentMatchInfo,
    PaymentCheckResponse,
    PaymentConfirmRequest,
    PaymentConfirmResponse,
)


class PaymentService:
    @staticmethod
    def check_payment_for_company(
        db: Session,
        company_id: int,
        req: PaymentCheckRequest,
    ) -> PaymentCheckResponse:
        """
        Try to find a matching payment for a given company and request.

        See module-level docstring for rules.
        """
        # compute cutoff time
        max_age = req.max_age_minutes or 30
        cutoff = datetime.utcnow() - timedelta(minutes=max_age)

        q = (
            db.query(Payment)
            .filter(
                Payment.company_id == company_id,
                Payment.created_at >= cutoff,
            )
            .filter(Payment.status != "used")
        )

        if req.txn_id is not None:
            q = q.filter(Payment.txn_id == req.txn_id)

        # order by newest first
        payment: Optional[Payment] = q.order_by(Payment.created_at.desc()).first()

        if payment is None:
            return PaymentCheckResponse(found=False, match=False)

        # build match info for response
        match_info = PaymentMatchInfo(
            payment_id=payment.id,
            txn_id=payment.txn_id,
            amount=payment.amount,
            currency=payment.currency,
            created_at=payment.created_at or datetime.utcnow(),
        )

        # amount mismatch: do not change status or confirm_token
        if payment.amount != req.expected_amount:
            return PaymentCheckResponse(
                found=True,
                match=False,
                reason="amount_mismatch",
                payment=match_info,
            )

        # full match: update payment to pending_confirmation and set confirm_token
        confirm_token = secrets.token_urlsafe(32)
        payment.status = "pending_confirmation"
        payment.order_id = req.order_id
        payment.confirm_token = confirm_token

        db.add(payment)
        db.commit()
        db.refresh(payment)

        match_info = PaymentMatchInfo(
            payment_id=payment.id,
            txn_id=payment.txn_id,
            amount=payment.amount,
            currency=payment.currency,
            created_at=payment.created_at,
        )

        return PaymentCheckResponse(
            found=True,
            match=True,
            confirm_token=confirm_token,
            order_id=payment.order_id,
            payment=match_info,
        )

    @staticmethod
    def confirm_payment_for_company(
        db: Session,
        company_id: int,
        req: PaymentConfirmRequest,
    ) -> PaymentConfirmResponse:
        """
        Confirm a payment using payment_id and confirm_token for a given company.
        """
        payment: Optional[Payment] = (
            db.query(Payment)
            .filter(
                Payment.id == req.payment_id,
                Payment.company_id == company_id,
            )
            .first()
        )

        if payment is None or payment.confirm_token != req.confirm_token:
            raise ValueError("Invalid payment_id or confirm_token")

        # idempotent behavior: already used
        if payment.status == "used":
            return PaymentConfirmResponse(
                success=True,
                already_used=True,
                payment_id=payment.id,
                status=payment.status,
            )

        # normal confirm flow
        payment.status = "used"
        payment.used_at = datetime.utcnow()
        db.add(payment)
        db.commit()
        db.refresh(payment)

        return PaymentConfirmResponse(
            success=True,
            already_used=False,
            payment_id=payment.id,
            status=payment.status,
        )

# Refactored by Copilot – Payment Service Feature
"""Payment service helpers and domain logic.

This module contains helpers to create payments from SMS payloads,
match payments to orders, and mark/confirm payment usage.

All changes here are non-destructive: docstrings and type hints only.
"""
import uuid
from sqlalchemy.orm import Session
from app.models.payment import Payment
from datetime import datetime, timedelta, timezone
from typing import Optional

import app.repositories.payment_repository as payment_repository
from app.services.wallet_service import update_wallet_usage
import logging

logger = logging.getLogger("payment_gateway")


def create_payment_from_sms(db: Session, payment_data: dict) -> Payment:
    """Create and persist a Payment from a normalized payment_data mapping.

    Args:
        db: SQLAlchemy `Session` used to persist the Payment.
        payment_data: Mapping of Payment fields (company_id, channel_id, amount, etc.).

    Returns:
        The persisted `Payment` instance (same object passed through SQLAlchemy session).

    Notes:
        This is a thin wrapper around SQLAlchemy model construction and session
        commit/refresh; it intentionally does not apply business rules.
    """
    # Filter out any keys that are not actual Payment columns to avoid
    # SQLAlchemy TypeError when unknown kwargs are passed to the model.
    allowed_fields = {c.key for c in Payment.__table__.columns}
    filtered_data = {k: v for k, v in payment_data.items() if k in allowed_fields}

    extra_keys = set(payment_data.keys()) - allowed_fields
    if extra_keys:
        logger.debug("Dropping extra payment fields: %s", sorted(extra_keys))

    payment = Payment(**filtered_data)
    # Delegate persistence to the repository
    return payment_repository.create(db, payment)


def match_payment_for_order(
    db: Session,
    company_id: int,
    amount: float,
    currency: str,
    payer_phone: Optional[str] = None,
    max_age_minutes: Optional[int] = None,
) -> Optional[Payment]:
    """Find a recent payment matching the provided criteria.

    Args:
        db: SQLAlchemy `Session` used to query payments.
        company_id: Company identifier to scope payment search.
        amount: Expected payment amount (used for tolerance checks elsewhere).
        currency: Currency code to match (e.g., 'USD').
        payer_phone: Optional phone number to further scope results.
        max_age_minutes: If provided, restrict to payments created within this many minutes.

    Returns:
        The most-recent `Payment` matching the criteria, or `None` when no candidate found.
    """
    # Delegate querying to the repository (keeps same filtering & ordering logic)
    return payment_repository.find_most_recent_matching(
        db=db,
        company_id=company_id,
        currency=currency,
        payer_phone=payer_phone,
        max_age_minutes=max_age_minutes,
    )


def generate_confirm_token() -> str:
    """Generate a short, URL-safe confirmation token for pending confirmation flows."""
    return uuid.uuid4().hex


def mark_payment_pending_confirmation(db: Session, payment: Payment) -> Payment:
    """Mark the given `payment` as pending confirmation and persist a confirm token.

    This mutates the provided `payment` instance, persists it via the session,
    and returns the refreshed object.
    """
    payment.status = "pending_confirmation"
    payment.confirm_token = generate_confirm_token()
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def confirm_payment_usage(db: Session, payment: Payment) -> Payment:
    """Confirm the usage of a payment.

    Actions performed:
    - set `payment.status = 'used'`
    - set `payment.used_at` to now
    - persist changes
    - if `payment.wallet_id` is present, call `update_wallet_usage` to reflect
      the consumed amount against the wallet.

    Returns the refreshed `Payment` instance.
    """
    payment.status = "used"
    # Use timezone-aware UTC timestamp
    payment.used_at = datetime.now(timezone.utc)
    db.add(payment)
    db.commit()
    db.refresh(payment)

    if payment.wallet_id:
        # Update wallet usage (implementation provided by wallet_service)
        update_wallet_usage(db, payment.wallet_id, payment.amount)

    return payment
