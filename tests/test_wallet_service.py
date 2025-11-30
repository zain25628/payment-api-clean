from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.models.company import Company
from app.models.wallet import Wallet
from app.models.payment import Payment
from app.models.channel import Channel
from app.models.country import PaymentProvider
from app.services.wallet_service import WalletService


def create_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # import models so they register
    import importlib

    importlib.import_module("app.models.company")
    importlib.import_module("app.models.wallet")
    importlib.import_module("app.models.payment")
    importlib.import_module("app.models.channel")
    importlib.import_module("app.models.country")

    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_pick_wallet_returns_wallet_under_daily_limit():
    db = create_test_db()
    company = Company(name="C1", api_key="k1")
    db.add(company)
    db.commit()

    w = Wallet(company_id=company.id, channel_id=1, wallet_label="W1", wallet_identifier="1001", daily_limit=500, is_active=True)
    db.add(w)
    db.commit()

    picked = WalletService.pick_wallet_for_company(db=db, company_id=company.id, amount=100)
    assert picked is not None
    assert picked.id == w.id


def test_pick_wallet_skips_wallet_over_daily_limit():
    db = create_test_db()
    company = Company(name="C2", api_key="k2")
    db.add(company)
    db.commit()

    w = Wallet(company_id=company.id, channel_id=1, wallet_label="W1", wallet_identifier="1001", daily_limit=500, is_active=True)
    db.add(w)
    db.commit()

    # create a payment today that uses 450
    p = Payment(company_id=company.id, wallet_id=w.id, amount=450, currency="AED", raw_message="x")
    db.add(p)
    db.commit()

    picked = WalletService.pick_wallet_for_company(db=db, company_id=company.id, amount=100)
    assert picked is None


def test_pick_wallet_chooses_less_used_wallet():
    db = create_test_db()
    company = Company(name="C3", api_key="k3")
    db.add(company)
    db.commit()

    w1 = Wallet(company_id=company.id, channel_id=1, wallet_label="W1", wallet_identifier="1001", daily_limit=500, is_active=True)
    w2 = Wallet(company_id=company.id, channel_id=1, wallet_label="W2", wallet_identifier="1002", daily_limit=500, is_active=True)
    db.add_all([w1, w2])
    db.commit()

    # add payment to w1
    p = Payment(company_id=company.id, wallet_id=w1.id, amount=100, currency="AED", raw_message="x")
    db.add(p)
    db.commit()

    picked = WalletService.pick_wallet_for_company(db=db, company_id=company.id, amount=50)
    assert picked is not None
    assert picked.id == w2.id
from datetime import date, timedelta
import pytest

from app.services import wallet_service
from app.models.wallet import Wallet


class _FakeSession:
    def __init__(self, wallet=None):
        self._added = []
        self.commits = 0
        self._wallet = wallet

    def add(self, obj):
        self._added.append(obj)

    def commit(self):
        self.commits += 1

    def refresh(self, obj):
        # no-op for fake session
        return obj

    class _FakeQuery:
        def __init__(self, result):
            self._result = result

        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def all(self):
            # if _result is a list, return as-is, else wrap
            return self._result if isinstance(self._result, list) else [self._result]

        def first(self):
            return self._result

    def query(self, model):
        return _FakeSession._FakeQuery(self._wallet)


def test_reset_wallet_if_needed_resets_on_new_day():
    # wallet with last_reset_date yesterday and used_today > 0
    w = Wallet()
    w.used_today = 10.0
    w.last_reset_date = date.today() - timedelta(days=1)

    db = _FakeSession()

    wallet_service.reset_wallet_if_needed(w, db)

    assert w.used_today == 0.0
    assert w.last_reset_date == date.today()
    assert db.commits >= 1


def test_reset_wallet_if_needed_same_day_no_reset():
    w = Wallet()
    w.used_today = 5.0
    w.last_reset_date = date.today()

    db = _FakeSession()

    wallet_service.reset_wallet_if_needed(w, db)

    assert w.used_today == 5.0
    # No commit when no changes needed
    assert db.commits == 0


def test_update_wallet_usage_increments_and_resets_if_needed(monkeypatch):
    # prepare a wallet with an old last_reset_date
    w = Wallet()
    w.id = 7
    w.used_today = 0.0
    w.last_reset_date = date.today() - timedelta(days=2)
    w.daily_limit = 100.0

    # FakeSession will return this wallet from query().first()
    db = _FakeSession(wallet=w)

    # Call update_wallet_usage
    updated = wallet_service.update_wallet_usage(db, wallet_id=7, amount=20.0)

    # wallet should have been reset then incremented
    assert updated is w
    assert w.last_reset_date == date.today()


def test_pick_wallet_with_preferred_payment_method_match():
    """Test that preferred_payment_method filters to matching provider."""
    db = create_test_db()
    
    # Create company
    company = Company(name="C_PPM", api_key="k_ppm")
    db.add(company)
    db.commit()
    
    # Create two payment providers
    provider1 = PaymentProvider(code="eand_money", name="EandMoney")
    provider2 = PaymentProvider(code="stripe", name="Stripe")
    db.add_all([provider1, provider2])
    db.commit()
    
    # Create channels for each provider
    channel1 = Channel(
        company_id=company.id,
        name="Channel1",
        channel_api_key="ch1",
        provider_id=provider1.id,
        is_active=True
    )
    channel2 = Channel(
        company_id=company.id,
        name="Channel2",
        channel_api_key="ch2",
        provider_id=provider2.id,
        is_active=True
    )
    db.add_all([channel1, channel2])
    db.commit()
    
    # Create wallets for each channel
    w1 = Wallet(
        company_id=company.id,
        channel_id=channel1.id,
        wallet_label="W_eand",
        wallet_identifier="eand_001",
        daily_limit=500,
        is_active=True
    )
    w2 = Wallet(
        company_id=company.id,
        channel_id=channel2.id,
        wallet_label="W_stripe",
        wallet_identifier="stripe_001",
        daily_limit=500,
        is_active=True
    )
    db.add_all([w1, w2])
    db.commit()
    
    # Request with preferred_payment_method="eand_money" should return w1
    picked = WalletService.pick_wallet_for_company(
        db=db,
        company_id=company.id,
        amount=100,
        preferred_payment_method="eand_money"
    )
    assert picked is not None
    assert picked.id == w1.id
    assert picked.channel.provider.code == "eand_money"


def test_pick_wallet_with_preferred_payment_method_no_match():
    """Test that preferred_payment_method returns None when no matching wallet exists."""
    db = create_test_db()
    
    # Create company
    company = Company(name="C_PPM_NO", api_key="k_ppm_no")
    db.add(company)
    db.commit()
    
    # Create one payment provider
    provider1 = PaymentProvider(code="stripe", name="Stripe")
    db.add(provider1)
    db.commit()
    
    # Create channel for stripe
    channel1 = Channel(
        company_id=company.id,
        name="Channel1",
        channel_api_key="ch1_no",
        provider_id=provider1.id,
        is_active=True
    )
    db.add(channel1)
    db.commit()
    
    # Create wallet for stripe
    w1 = Wallet(
        company_id=company.id,
        channel_id=channel1.id,
        wallet_label="W_stripe",
        wallet_identifier="stripe_001",
        daily_limit=500,
        is_active=True
    )
    db.add(w1)
    db.commit()
    
    # Request with preferred_payment_method="eand_money" should return None (no match)
    picked = WalletService.pick_wallet_for_company(
        db=db,
        company_id=company.id,
        amount=100,
        preferred_payment_method="eand_money"
    )
    assert picked is None
