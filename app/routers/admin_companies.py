from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import Company
from app.models.channel import Channel
from app.schemas.admin_company import (
    AdminCompanyCreate,
    AdminCompanyOut,
    AdminCompanyListItem,
    AdminChannelOut,
)
from app.services.admin_company_service import AdminCompanyService
from app.services.admin_onboarding_service import AdminOnboardingService
from app.schemas.admin_onboarding import AdminOnboardingGenerateResponse
from pathlib import Path


router = APIRouter(
    prefix="/admin/companies",
    tags=["admin-companies"],
)


def _company_to_admin_out(company: Company) -> AdminCompanyOut:
    channels_out: List[AdminChannelOut] = []
    for ch in company.channels:
        provider_code = ch.provider.code if ch.provider is not None else None
        provider_name = ch.provider.name if ch.provider is not None else None
        channels_out.append(
            AdminChannelOut(
                id=ch.id,
                name=ch.name,
                provider_code=provider_code,
                provider_name=provider_name,
                channel_api_key=ch.channel_api_key,
                telegram_group_id=ch.telegram_group_id,
                is_active=ch.is_active,
            )
        )
    # map wallets (if present) into admin wallet output
    wallets_out = []
    for w in getattr(company, 'wallets', []) or []:
        provider = None
        if w.channel and getattr(w.channel, 'provider', None) is not None:
            provider = w.channel.provider
        wallets_out.append(
            {
                'id': w.id,
                'wallet_label': w.wallet_label,
                'wallet_identifier': w.wallet_identifier,
                'daily_limit': w.daily_limit,
                'is_active': w.is_active,
                'channel_id': w.channel_id,
                'channel_name': w.channel.name if w.channel is not None else '',
                'provider_code': provider.code if provider is not None else None,
                'provider_name': provider.name if provider is not None else None,
            }
        )
    return AdminCompanyOut(
        id=company.id,
        name=company.name,
        api_key=company.api_key,
        is_active=company.is_active,
        country_code=company.country_code,
        telegram_bot_token=company.telegram_bot_token,
        telegram_default_group_id=company.telegram_default_group_id,
        channels=channels_out,
        wallets=wallets_out,
    )


@router.post("/", response_model=AdminCompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    data: AdminCompanyCreate,
    db: Session = Depends(get_db),
):
    company = AdminCompanyService.create_company_with_channels(db, data)
    # Provision onboarding artifacts (default channel + wallet) for convenience.
    # Keep this router-level so unit tests calling the service directly are unaffected.
    company = AdminCompanyService.provision_onboarding(db, company)
    db.refresh(company)
    return _company_to_admin_out(company)


@router.get("/", response_model=List[AdminCompanyListItem])
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.id.asc()).all()
    return [
        AdminCompanyListItem(
            id=c.id,
            name=c.name,
            country_code=c.country_code,
            is_active=c.is_active,
        )
        for c in companies
    ]


@router.get("/{company_id}", response_model=AdminCompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    _ = company.channels
    return _company_to_admin_out(company)


@router.put("/{company_id}", response_model=AdminCompanyOut)
def update_company(
    company_id: int,
    data: AdminCompanyCreate,
    db: Session = Depends(get_db),
):
    """
    Update an existing company and its channels based on AdminCompanyCreate payload.

    - Uses AdminCompanyService.update_company_and_channels.
    - Returns 404 if the company does not exist.
    """
    company = AdminCompanyService.update_company_and_channels(db, company_id=company_id, data=data)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    # ensure relationships are loaded
    _ = company.channels
    return _company_to_admin_out(company)


@router.post("/{company_id}/toggle", response_model=AdminCompanyOut)
def toggle_company_active(
    company_id: int,
    db: Session = Depends(get_db),
):
    """
    Flip the is_active flag for the given company.
    """
    company = AdminCompanyService.toggle_company_active(db, company_id=company_id)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    # ensure channels are loaded
    _ = company.channels
    return _company_to_admin_out(company)




@router.post("/{company_id}/onboarding-pdf", response_model=AdminOnboardingGenerateResponse)
def generate_onboarding_pdf(
    company_id: int,
    db: Session = Depends(get_db),
):
    return AdminOnboardingService.generate_company_onboarding_pdf(db, company_id)
