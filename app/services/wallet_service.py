
# Refactored by Copilot – Wallet Service Feature
"""Wallet-related domain helpers.

This module provides small utilities around wallet usage tracking and
selection. Changes here are limited to type hints and docstrings; behavior
and signatures are preserved.
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import date
from app.models.wallet import Wallet
from sqlalchemy import asc

import app.repositories.wallet_repository as wallet_repository
from datetime import datetime, time
from typing import List
from app.models.payment import Payment


def reset_wallet_if_needed(wallet: Wallet, db: Session) -> None:
    """Reset a wallet's daily usage if the last reset date is before today.

    Args:
        wallet: `Wallet` instance to inspect and potentially reset.
        db: SQLAlchemy `Session` used to persist changes when a reset occurs.

    Behavior:
        - If `wallet.last_reset_date` is None or older than today, set
          `wallet.used_today = 0.0` and update `wallet.last_reset_date` to today,
          then persist via `db.add`, `db.commit`, `db.refresh`.
        - Otherwise perform no changes.
    """
    today = date.today()
    if wallet.last_reset_date is None or wallet.last_reset_date < today:
        wallet.used_today = 0.0
        wallet.last_reset_date = today
        db.add(wallet)
        db.commit()
        db.refresh(wallet)


def find_available_wallet(db: Session, company_id: int, amount: float) -> Optional[Wallet]:
    """Return the first active wallet for `company_id` that can accept `amount`.

    The selection iterates wallets ordered by `id`, resets daily usage if needed,
    and returns the first wallet where `used_today + amount <= daily_limit`.

    Returns:
        A `Wallet` instance when found, otherwise `None`.
    """
    wallets = wallet_repository.get_company_active_wallets(db, company_id)

    for wallet in wallets:
        reset_wallet_if_needed(wallet, db)
        if wallet.used_today + amount <= wallet.daily_limit:
            return wallet
    return None


def update_wallet_usage(db: Session, wallet_id: int, amount: float) -> Optional[Wallet]:
    """Increment `used_today` on the wallet and persist changes.

    Args:
        db: SQLAlchemy `Session` used to query and persist the wallet.
        wallet_id: Identifier of the wallet to update.
        amount: Amount to add to the wallet's `used_today`.

    Returns:
        The updated `Wallet` when found and updated; otherwise `None`.
    """
    wallet = wallet_repository.get_by_id(db, wallet_id)
    if wallet:
        reset_wallet_if_needed(wallet, db)
        
        # Atomic update to prevent race conditions
        result = db.query(Wallet).filter(
            Wallet.id == wallet_id,
            Wallet.used_today + amount <= Wallet.daily_limit
        ).update(
            {"used_today": Wallet.used_today + amount},
            synchronize_session=False
        )
        
        if result == 0:
            # Check if it failed because of limit or missing (we know it exists from get_by_id)
            # Since we just fetched it, it's likely the limit.
            # Refresh to see current state
            db.refresh(wallet)
            if wallet.used_today + amount > wallet.daily_limit:
                raise ValueError("Daily limit exceeded")
            # If result is 0 but limit not exceeded, something else happened (deleted?), return None
            return None

        db.commit()
        db.refresh(wallet)
        return wallet
    return None


class WalletService:
    @staticmethod
    def pick_wallet_for_company(
        db: Session,
        company_id: int,
        amount: float,
        preferred_payment_method: Optional[str] = None,
    ) -> Optional[Wallet]:
        """
        Choose an appropriate wallet for a company and amount.

        Rules:
        - Wallet must be active and belong to the company (retrieved via repository).
        - We compute total amount for the wallet for the current UTC date by summing
          Payment.amount for payments created today for that wallet.
        - If total_today + amount > daily_limit -> wallet is not eligible.
        - If multiple eligible, pick the one with smallest total_today.
        - If preferred_payment_method is set, only wallets associated with that
          payment provider (by code) are considered.
        """
        wallets: List[Wallet] = wallet_repository.get_company_active_wallets(db, company_id)
        if not wallets:
            return None

        # Filter by preferred payment method if specified
        if preferred_payment_method is not None:
            wallets = [
                w for w in wallets
                if w.channel and w.channel.provider and w.channel.provider.code == preferred_payment_method
            ]
            if not wallets:
                return None

        today = datetime.utcnow().date()
        candidates = []

        start_dt = datetime.combine(today, time.min)
        end_dt = datetime.combine(today, time.max)

        for w in wallets:
            # Sum payments for this wallet today
            total_rows = (
                db.query(Payment.amount)
                .filter(
                    Payment.wallet_id == w.id,
                    Payment.created_at >= start_dt,
                    Payment.created_at <= end_dt,
                )
                .all()
            )
            sum_today = sum(r[0] for r in total_rows) if total_rows else 0

            # If wallet has daily_limit and would be exceeded, skip
            if w.daily_limit is not None and (sum_today + amount) > float(w.daily_limit):
                continue

            candidates.append((w, sum_today))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[1])
        return candidates[0][0]
