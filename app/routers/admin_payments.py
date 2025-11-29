from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.payment_repository import query_payments
from app.schemas.admin_payment import PaginatedPaymentsResponse, PaymentAdminSummary
from app.models.payment import Payment


router = APIRouter(
    prefix="/admin/payments",
    tags=["admin-payments"],
)


@router.get("/", response_model=PaginatedPaymentsResponse)
def list_payments(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    created_from: Optional[datetime] = Query(None),
    created_to: Optional[datetime] = Query(None),
    company_id: Optional[int] = Query(None),
    channel_id: Optional[int] = Query(None),
    wallet_id: Optional[int] = Query(None),
    txn_id: Optional[str] = Query(None),
):
    items, total = query_payments(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        min_amount=min_amount,
        max_amount=max_amount,
        created_from=created_from,
        created_to=created_to,
        company_id=company_id,
        channel_id=channel_id,
        wallet_id=wallet_id,
        txn_id=txn_id,
    )

    out_items = []
    for p in items:
        out_items.append(
            PaymentAdminSummary(
                payment_id=p.id,
                company_id=p.company_id,
                company_name=getattr(p.company, "name", None),
                channel_id=p.channel_id,
                channel_name=getattr(p.channel, "name", None) if getattr(p, "channel", None) is not None else None,
                wallet_id=p.wallet_id,
                txn_id=p.txn_id,
                amount=p.amount,
                currency=p.currency,
                status=p.status,
                payer_phone=p.payer_phone,
                created_at=p.created_at,
                used_at=p.used_at,
            )
        )

    return PaginatedPaymentsResponse(items=out_items, total=total, page=page, page_size=page_size)
