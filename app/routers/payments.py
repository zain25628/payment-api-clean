from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
try:
    # Prefer the legacy deps implementation so tests that override that callable
    # (in tests/conftest.py) continue to work. If you want to explicitly use the
    # new company_auth dependency, import it directly elsewhere.
    from app.dependencies.deps import get_current_company
except Exception:
    from app.dependencies.company_auth import get_current_company
from app.models.company import Company
from app.schemas.payment_api import (
    PaymentCheckRequest,
    PaymentCheckResponse,
    PaymentConfirmRequest,
    PaymentConfirmResponse,
)
from app.services.payment_service import PaymentService
import app.services.payment_service as payment_service
from pydantic import BaseModel, Field
from typing import Optional


router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


@router.post("/check", response_model=PaymentCheckResponse)
def check_payment(
    payload: PaymentCheckRequest,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    """
    Check if there is a matching payment for the current company and request payload.
    """
    resp = PaymentService.check_payment_for_company(
        db=db,
        company_id=current_company.id,
        req=payload,
    )
    return resp


@router.post("/confirm", response_model=PaymentConfirmResponse)
def confirm_payment(
    payload: PaymentConfirmRequest,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    """
    Confirm a previously matched payment using payment_id and confirm_token.
    """
    try:
        resp = PaymentService.confirm_payment_for_company(
            db=db,
            company_id=current_company.id,
            req=payload,
        )
        return resp
    except ValueError as exc:
        # invalid payment_id or confirm_token
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# Legacy / additional endpoints (kept for backward compatibility)
class PaymentMatchRequest(BaseModel):
    order_id: Optional[str] = Field(default=None)
    txn_id: Optional[str] = Field(default=None)
    amount: float = Field(...)
    currency: Optional[str] = Field(default="USD")
    payer_phone: Optional[str] = None


class PaymentMatchResponse(BaseModel):
    found: bool
    match: bool
    payment_id: Optional[int] = None
    txn_id: Optional[str] = None
    status: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    payment_id: int
    status: str


@router.post("/match", response_model=PaymentMatchResponse)
def payments_match(
    payload: PaymentMatchRequest,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    payment = payment_service.match_payment_for_order(
        db,
        company.id,
        float(payload.amount),
        payload.currency or "USD",
        payload.payer_phone,
    )

    if payment is None:
        return PaymentMatchResponse(found=False, match=False)

    if abs(payment.amount - float(payload.amount)) > 0.01:
        return PaymentMatchResponse(found=True, match=False, payment_id=payment.id, txn_id=payment.txn_id, status=payment.status)

    return PaymentMatchResponse(found=True, match=True, payment_id=payment.id, txn_id=payment.txn_id, status=payment.status)


@router.post("/{payment_id}/pending-confirmation", response_model=PaymentStatusResponse)
def payments_pending_confirmation(
    payment_id: int,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    payment = db.query(payment_service.Payment).filter(payment_service.Payment.id == payment_id, payment_service.Payment.company_id == company.id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment = payment_service.mark_payment_pending_confirmation(db, payment)
    return PaymentStatusResponse(payment_id=payment.id, status=payment.status)


@router.post("/{payment_id}/confirm-usage", response_model=PaymentStatusResponse)
def payments_confirm_usage(
    payment_id: int,
    db: Session = Depends(get_db),
    company: Company = Depends(get_current_company),
):
    payment = db.query(payment_service.Payment).filter(payment_service.Payment.id == payment_id, payment_service.Payment.company_id == company.id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment = payment_service.confirm_payment_usage(db, payment)
    return PaymentStatusResponse(payment_id=payment.id, status=payment.status)

# Refactored by Copilot – Payments Feature
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

