from sqlalchemy.orm import Session
import secrets
from typing import Iterable, Dict

from app.models.company import Company
from app.models.channel import Channel
from app.models.wallet import Wallet
from app.models.country import PaymentProvider
from app.schemas.admin_company import AdminCompanyCreate
from app.config import settings


class AdminCompanyService:
    @staticmethod
    def generate_api_key() -> str:
        """Generate a random API key string."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def _get_providers_by_codes(db: Session, provider_codes: Iterable[str]) -> Dict[str, PaymentProvider]:
        if not provider_codes:
            return {}
        providers = (
            db.query(PaymentProvider)
            .filter(PaymentProvider.code.in_(list(provider_codes)))
            .all()
        )
        return {p.code: p for p in providers}

    @staticmethod
    def create_company_with_channels(db: Session, data: AdminCompanyCreate) -> Company:
        """
        Create a new Company and its Channels based on the selected provider codes.

        - Generates a company API key.
        - Persists the company.
        - Looks up PaymentProvider rows by `data.provider_codes`.
        - For each found provider, creates a Channel linked to the company.
        """
        # 1) create the Company
        api_key = AdminCompanyService.generate_api_key()
        company = Company(
            name=data.name,
            api_key=api_key,
            country_code=data.country_code,
            telegram_bot_token=data.telegram_bot_token,
            telegram_default_group_id=data.telegram_default_group_id,
            is_active=True,
        )
        db.add(company)
        db.flush()  # obtain company.id

        # 2) prepare providers
        providers_by_code = AdminCompanyService._get_providers_by_codes(db, data.provider_codes)

        # 3) create channels for each existing provider
        for code in data.provider_codes:
            provider = providers_by_code.get(code)
            if provider is None:
                # unknown provider: ignore silently
                continue

            channel = Channel(
                company_id=company.id,
                name=f"{provider.name} Channel",
                provider=provider,
                channel_api_key=AdminCompanyService.generate_api_key(),
                is_active=True,
            )
            db.add(channel)

        # 4) commit and refresh company
        db.commit()
        db.refresh(company)
        return company

    @staticmethod
    def provision_onboarding(db: Session, company: Company) -> Company:
        """
        Provision a primary channel and wallet for a newly-created company.

        This method is intentionally separate from `create_company_with_channels`
        so unit tests that call the service directly are not affected.
        """
        # create a default channel only if the company has no channels
        existing_channels = db.query(Channel).filter(Channel.company_id == company.id).all()
        if not existing_channels:
            default_channel = Channel(
                company_id=company.id,
                name="Primary Channel",
                channel_api_key=AdminCompanyService.generate_api_key(),
                is_active=True,
            )
            db.add(default_channel)
            db.flush()
            channel_to_use = default_channel
        else:
            channel_to_use = existing_channels[0]

        # create a default wallet if none exist
        existing_wallets = db.query(Wallet).filter(Wallet.company_id == company.id).all()
        if not existing_wallets:
            default_wallet = Wallet(
                company_id=company.id,
                channel_id=channel_to_use.id,
                wallet_label=f"Default Wallet",
                wallet_identifier=f"WALLET-{company.id}-1",
                daily_limit=getattr(settings, 'DEFAULT_WALLET_DAILY_LIMIT', 100000.0),
                is_active=True,
            )
            db.add(default_wallet)

        db.commit()
        db.refresh(company)
        return company

    @staticmethod
    def update_company_and_channels(
        db: Session,
        company_id: int,
        data: AdminCompanyCreate,
    ) -> Company | None:
        """
        Update an existing Company and adjust its Channels based on the selected provider codes.

        - Updates basic company fields (name, country_code, telegram_*).
        - Loads existing channels for the company.
        - Ensures channels exist and are active for the selected providers.
        - Deactivates channels for providers that are no longer selected.
        - Ignores unknown provider codes (that don't exist in PaymentProvider).
        """
        company: Company | None = (
            db.query(Company).filter(Company.id == company_id).first()
        )
        if company is None:
            return None

        # update basic fields
        company.name = data.name
        company.country_code = data.country_code
        company.telegram_bot_token = data.telegram_bot_token
        company.telegram_default_group_id = data.telegram_default_group_id

        # prepare desired providers (ignore unknown codes)
        providers_by_code = AdminCompanyService._get_providers_by_codes(db, data.provider_codes)
        desired_providers = [providers_by_code[c] for c in data.provider_codes if c in providers_by_code]

        # load existing channels for the company
        existing_channels: list[Channel] = (
            db.query(Channel)
            .filter(Channel.company_id == company.id)
            .all()
        )

        # map provider_id -> channel
        channels_by_provider_id: dict[int, Channel] = {}
        for ch in existing_channels:
            if ch.provider_id is not None:
                channels_by_provider_id[ch.provider_id] = ch

        # ensure channels for desired providers
        for provider in desired_providers:
            ch = channels_by_provider_id.get(provider.id)
            if ch is not None:
                ch.is_active = True
            else:
                new_ch = Channel(
                    company_id=company.id,
                    name=f"{provider.name} Channel",
                    provider=provider,
                    channel_api_key=AdminCompanyService.generate_api_key(),
                    is_active=True,
                )
                db.add(new_ch)

        # deactivate channels for providers that are no longer desired
        desired_provider_ids = {p.id for p in desired_providers}
        for ch in existing_channels:
            if ch.provider_id is None:
                continue
            if ch.provider_id not in desired_provider_ids:
                ch.is_active = False

        db.commit()
        db.refresh(company)
        return company

    @staticmethod
    def toggle_company_active(db: Session, company_id: int) -> Company | None:
        """
        Flip the is_active flag for a company.

        Returns the updated Company, or None if not found.
        """
        company: Company | None = (
            db.query(Company).filter(Company.id == company_id).first()
        )
        if company is None:
            return None

        company.is_active = not company.is_active
        db.commit()
        db.refresh(company)
        return company
