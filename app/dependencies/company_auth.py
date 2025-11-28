from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import Company


def get_company_by_api_key(db: Session, api_key: str) -> Company:
    """
    Low-level helper: fetch a Company by its api_key or raise HTTP 401/403.
    - 401 if missing/invalid key.
    - 403 if company exists but is not active.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key",
        )

    company = (
        db.query(Company)
        .filter(Company.api_key == api_key)
        .first()
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-API-Key",
        )

    if not company.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company is inactive",
        )

    return company


def get_current_company(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Company:
    """
    FastAPI dependency to resolve the current Company from the X-API-Key header.
    This will be used by public APIs (e.g. /payments/check, /payments/confirm).
    """
    return get_company_by_api_key(db=db, api_key=x_api_key)
