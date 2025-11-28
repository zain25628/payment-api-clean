# Refactored by Copilot
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.config import settings, get_settings


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    wallet_label = Column(String, nullable=False)
    wallet_identifier = Column(String, nullable=False)
    daily_limit = Column(Float, default=0.0)
    used_today = Column(Float, default=0.0)
    last_reset_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    # Use CURRENT_TIMESTAMP for server-side defaults (works on SQLite)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), onupdate=func.current_timestamp(), server_default=func.current_timestamp())

    company = relationship("Company", back_populates="wallets")
    channel = relationship("Channel", back_populates="wallets")
    payments = relationship("Payment", back_populates="wallet")
