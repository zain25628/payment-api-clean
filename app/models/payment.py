from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=True)

    amount = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, default="AED")

    txn_id = Column(String, index=True, nullable=True)
    payer_phone = Column(String, nullable=True)
    receiver_phone = Column(String, nullable=True)

    raw_message = Column(String, nullable=False)

    status = Column(String, nullable=False, default="new")
    order_id = Column(String, nullable=True)
    confirm_token = Column(String, nullable=True, index=True)

    # Use CURRENT_TIMESTAMP for server-side defaults (compatible with SQLite)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), onupdate=func.current_timestamp(), server_default=func.current_timestamp())
    used_at = Column(DateTime(timezone=True), nullable=True)

    company = relationship("Company", back_populates="payments")
    channel = relationship("Channel", back_populates="payments")
    wallet = relationship("Wallet", back_populates="payments")

    def __init__(self, *args, **kwargs):
        # ensure a Python-side default for status when instantiating without DB
        if "status" not in kwargs:
            kwargs["status"] = "new"
        super().__init__(*args, **kwargs)
