# Refactored by Copilot
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.config import settings, get_settings


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    provider_id = Column(Integer, ForeignKey("payment_providers.id"), nullable=True)
    channel_api_key = Column(String, unique=True, index=True, nullable=False)
    telegram_group_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    # Use CURRENT_TIMESTAMP for DB compatibility (SQLite, Postgres, MySQL)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), onupdate=func.current_timestamp(), server_default=func.current_timestamp())

    company = relationship("Company", back_populates="channels")
    provider = relationship("PaymentProvider", backref="channels")
    wallets = relationship("Wallet", back_populates="channel")
    payments = relationship("Payment", back_populates="channel")
