from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from pie.db import get_db
from pie.models import ApiKey, Company


def require_company(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Company:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization: Bearer <api_key>")

    key = authorization.split(" ", 1)[1].strip()
    api_key = db.get(ApiKey, key)
    if not api_key or api_key.revoked:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    company = db.get(Company, api_key.company_id)
    if not company:
        raise HTTPException(status_code=401, detail="Company not found for this key")

    return company


def require_tier(min_tier: str):
    order = {"free": 0, "pro": 1, "enterprise": 2}
    needed = order[min_tier]

    def _dep(company: Company = Depends(require_company)) -> Company:
        if order.get(company.tier, 0) < needed:
            raise HTTPException(status_code=402, detail=f"Upgrade required: {min_tier}+")
        return company

    return _dep
