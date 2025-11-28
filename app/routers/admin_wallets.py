from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.wallet import Wallet
from app.models.channel import Channel
from app.models.payment import Payment
from app.schemas.admin_wallets import (
    AdminWalletCreate,
    AdminWalletOut,
    AdminWalletUpdate,
)


router = APIRouter(prefix="/admin", tags=["admin-wallets"])


def _wallet_to_out(w: Wallet) -> AdminWalletOut:
    provider = None
    if w.channel and getattr(w.channel, "provider", None) is not None:
        provider = w.channel.provider

    return AdminWalletOut(
        id=w.id,
        wallet_label=w.wallet_label,
        wallet_identifier=w.wallet_identifier,
        daily_limit=w.daily_limit,
        is_active=w.is_active,
        channel_id=w.channel_id,
        channel_name=w.channel.name if w.channel is not None else "",
        provider_code=provider.code if provider is not None else None,
        provider_name=provider.name if provider is not None else None,
    )


@router.get("/companies/{company_id}/wallets", response_model=List[AdminWalletOut])
def list_company_wallets(company_id: int, db: Session = Depends(get_db)):
    wallets = db.query(Wallet).filter(Wallet.company_id == company_id).order_by(Wallet.id.asc()).all()
    return [_wallet_to_out(w) for w in wallets]


@router.post("/companies/{company_id}/wallets", response_model=AdminWalletOut, status_code=status.HTTP_201_CREATED)
def create_company_wallet(company_id: int, data: AdminWalletCreate, db: Session = Depends(get_db)):
    # ensure channel exists and belongs to company
    channel = db.query(Channel).filter(Channel.id == data.channel_id, Channel.company_id == company_id).first()
    if not channel:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Channel not found for company")

    wallet = Wallet(
        company_id=company_id,
        channel_id=data.channel_id,
        wallet_label=data.wallet_label,
        wallet_identifier=data.wallet_identifier,
        daily_limit=data.daily_limit,
        is_active=data.is_active,
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return _wallet_to_out(wallet)


@router.put("/wallets/{wallet_id}", response_model=AdminWalletOut)
def update_wallet(wallet_id: int, data: AdminWalletUpdate, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    if data.wallet_label is not None:
        wallet.wallet_label = data.wallet_label
    if data.wallet_identifier is not None:
        wallet.wallet_identifier = data.wallet_identifier
    if data.daily_limit is not None:
        wallet.daily_limit = data.daily_limit
    if data.is_active is not None:
        wallet.is_active = data.is_active

    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return _wallet_to_out(wallet)


@router.post("/wallets/{wallet_id}/toggle", response_model=AdminWalletOut)
def toggle_wallet(wallet_id: int, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    wallet.is_active = not bool(wallet.is_active)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return _wallet_to_out(wallet)
