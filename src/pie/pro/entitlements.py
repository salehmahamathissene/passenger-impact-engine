from __future__ import annotations

from fastapi import Depends, HTTPException

from pie.pro.enterprise_routes import require_company
from pie.pro.enterprise_models import EnterpriseCompany

def require_paid_company(company: EnterpriseCompany = Depends(require_company)) -> EnterpriseCompany:
    plan = (getattr(company, "plan", None) or "free").lower()
    active = bool(getattr(company, "is_active", False)) and plan != "free"
    if not active:
        raise HTTPException(status_code=402, detail="Payment required")
    return company
