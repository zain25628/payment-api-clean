from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.admin_geo import (
    AdminCountryOut,
    AdminPaymentProviderOut,
    AdminCountryWithProviders,
    AdminCountryCreate,
)
from app.services.admin_geo_service import AdminGeoService


router = APIRouter(
    prefix="/admin/geo",
    tags=["admin-geo"],
)


@router.get("/countries", response_model=List[AdminCountryOut])
def list_countries(db: Session = Depends(get_db)):
    return AdminGeoService.list_countries(db)


@router.get("/providers", response_model=List[AdminPaymentProviderOut])
def list_payment_providers(db: Session = Depends(get_db)):
    return AdminGeoService.list_payment_providers(db)


@router.get("/countries/{country_code}/providers", response_model=AdminCountryWithProviders)
def get_country_with_providers(country_code: str, db: Session = Depends(get_db)):
    result = AdminGeoService.get_country_with_providers(db, country_code=country_code)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Country not found",
        )
    return result



@router.post("/countries", response_model=AdminCountryOut, status_code=201)
def create_country(payload: AdminCountryCreate, db: Session = Depends(get_db)):
    country = AdminGeoService.create_country(db, payload)
    return AdminCountryOut.model_validate(country)
