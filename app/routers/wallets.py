# Refactored by Copilot
"""
# Refactored by Copilot – Wallets Feature
Organize the `/wallets/request` endpoint to use Pydantic request/response
models and clear validation while preserving the existing wallet selection
logic in `find_available_wallet`.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.config import settings, get_settings
from app.db.session import get_db
from app.dependencies.deps import get_current_company
from app.models.company import Company
from app.models.wallet import Wallet
from app.services.wallet_service import WalletService
# keep backward-compatible symbol expected by older tests
def find_available_wallet(db, company_id, amount):
    return WalletService.pick_wallet_for_company(db=db, company_id=company_id, amount=amount)
from app.schemas.wallet_api import WalletRequestPayload, WalletRequestResponse


class WalletRequest(WalletRequestPayload):
    pass


class WalletResponse(WalletRequestResponse):
    pass


router = APIRouter(tags=["wallets"])


@router.post("/wallets/request", response_model=WalletResponse)
def request_wallet(
    payload: WalletRequest,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    """Select an available wallet for the requested amount for the current company.

    The endpoint depends on `X-API-Key` (resolved by `get_current_company`) to
    identify the company. The actual selection logic is delegated to
    `find_available_wallet` and is not changed here.

    Optional parameter:
        preferred_payment_method (optional string): provider code (e.g. "eand_money",
        "stripe", "ui-test"). When set, wallet selection is restricted to this provider.
    """
    amount = float(payload.amount)
    preferred_payment_method = payload.preferred_payment_method

    wallet = WalletService.pick_wallet_for_company(
        db=db,
        company_id=company.id,
        amount=amount,
        preferred_payment_method=preferred_payment_method,
    )
    if wallet is None:
        raise HTTPException(
            status_code=404,
            detail="No wallet available for this company / amount",
        )

    channel = wallet.channel
    if channel is None or not channel.is_active:
        raise HTTPException(
            status_code=400,
            detail="Wallet channel is not available",
        )

    return WalletResponse(
        wallet_id=wallet.id,
        wallet_identifier=wallet.wallet_identifier,
        wallet_label=wallet.wallet_label,
        channel_api_key=channel.channel_api_key,
        channel_id=channel.id,
    )
