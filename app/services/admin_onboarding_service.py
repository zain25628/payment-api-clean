from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services.admin_company_service import AdminCompanyService
from app.config import settings
from app.models.company import Company
from app.schemas.admin_onboarding import AdminOnboardingGenerateResponse

try:
    # import the generate_onboarding helper from repo root
    from generate_onboarding_pdf import generate_onboarding
except Exception:
    generate_onboarding = None


class AdminOnboardingService:
    @staticmethod
    def generate_company_onboarding_pdf(db: Session, company_id: int) -> AdminOnboardingGenerateResponse:
        # use existing service to load company
        company = db.query(Company).filter(Company.id == company_id).first()
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

        if not getattr(company, 'is_active', True):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company must be active to generate onboarding")

        merchant_name = company.name or f"company-{company.id}"
        api_key = company.api_key
        # pick base URL from settings; fall back to existing default
        base_url = getattr(settings, 'DEFAULT_MERCHANT_BASE_URL_DEV', 'http://localhost:8000')
        env = getattr(settings, 'ENVIRONMENT_NAME', 'dev')

        output_dir = Path(getattr(settings, 'ONBOARDING_OUTPUT_DIR', 'generated_onboarding'))
        output_dir.mkdir(parents=True, exist_ok=True)

        if generate_onboarding is None:
            # Attempt to at least populate HTML URL if possible by raising a 503 or generating HTML via other means.
            # Here we raise 503 to indicate generator isn't available on this host.
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Onboarding generator is not available on this server")

        html_path, pdf_path = generate_onboarding(
            merchant_name=merchant_name,
            api_key=api_key,
            base_url=base_url,
            environment=env,
            output_dir=output_dir,
        )

        html_name = Path(html_path).name
        pdf_name = Path(pdf_path).name if pdf_path is not None else None

        html_url = f"/static/onboarding/{html_name}"
        pdf_url = f"/static/onboarding/{pdf_name}" if pdf_name else None

        return AdminOnboardingGenerateResponse(
            company_id=company.id,
            html_path=str(html_path),
            pdf_path=str(pdf_path) if pdf_path is not None else None,
            html_url=html_url,
            pdf_url=pdf_url,
            environment=env,
        )
