from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services.admin_company_service import AdminCompanyService
from app.config import settings
from app.models.company import Company

try:
    # import the generate_onboarding helper from repo root
    from generate_onboarding_pdf import generate_onboarding
except Exception:
    generate_onboarding = None


class AdminOnboardingService:
    @staticmethod
    def generate_company_onboarding_pdf(db: Session, company_id: int) -> tuple:
        # use existing service to load company
        company = db.query(Company).filter(Company.id == company_id).first()
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

        if not getattr(company, 'is_active', True):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company must be active to generate onboarding")

        merchant_name = company.name or f"company-{company.id}"
        api_key = company.api_key
        base_url = getattr(settings, 'DEFAULT_MERCHANT_BASE_URL_DEV', 'http://localhost:8000')
        env = getattr(settings, 'ENVIRONMENT_NAME', 'dev')

        output_dir = Path(getattr(settings, 'ONBOARDING_OUTPUT_DIR', 'generated_onboarding'))
        output_dir.mkdir(parents=True, exist_ok=True)

        if generate_onboarding is None:
            # We cannot generate here; still render HTML via direct call to the script is not possible.
            # Raise a 503 to indicate the service is not available on this host.
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Onboarding generator is not available on this server")

        html_path, pdf_path = generate_onboarding(
            merchant_name=merchant_name,
            api_key=api_key,
            base_url=base_url,
            environment=env,
            output_dir=output_dir,
        )

        return company, html_path, pdf_path
