from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)

    country_providers = relationship("CountryPaymentProvider", back_populates="country")


class PaymentProvider(Base):
    __tablename__ = "payment_providers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    country_links = relationship("CountryPaymentProvider", back_populates="provider")


class CountryPaymentProvider(Base):
    __tablename__ = "country_payment_providers"
    __table_args__ = (UniqueConstraint("country_id", "provider_id", name="uq_country_provider"),)

    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("payment_providers.id"), nullable=False)
    is_supported = Column(Boolean, default=True, nullable=False)

    country = relationship("Country", back_populates="country_providers")
    provider = relationship("PaymentProvider", back_populates="country_links")
