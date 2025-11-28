from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.admin_geo import (
    AdminPaymentProviderOut,
    AdminPaymentProviderCreate,
)
from app.services.admin_geo_service import AdminGeoService


router = APIRouter(
    prefix="/admin",
    tags=["admin-payment-providers"],
)


@router.get("/payment-providers", response_model=List[AdminPaymentProviderOut])
def list_payment_providers(db: Session = Depends(get_db)):
    try:
        return AdminGeoService.list_payment_providers(db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post(
    "/payment-providers",
    response_model=AdminPaymentProviderOut,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_provider(
    data: AdminPaymentProviderCreate,
    db: Session = Depends(get_db),
):
    try:
        provider = AdminGeoService.create_payment_provider(db, data)
        return AdminPaymentProviderOut.model_validate(provider)
    except HTTPException:
        # re-raise known HTTP exceptions (e.g. 400 on duplicate code)
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
