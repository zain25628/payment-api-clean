# Refactored by Copilot
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.config import settings, get_settings


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    country_code = Column(String, nullable=True)
    telegram_bot_token = Column(String, nullable=True)
    telegram_default_group_id = Column(String, nullable=True)
    # Use CURRENT_TIMESTAMP for server defaults to be compatible with SQLite
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), onupdate=func.current_timestamp(), server_default=func.current_timestamp())

    channels = relationship("Channel", back_populates="company")
    wallets = relationship("Wallet", back_populates="company")
    payments = relationship("Payment", back_populates="company")
