from __future__ import annotations

import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from pie.db import get_db
from pie.models import Company, UsageEvent
from pie.api.auth import require_tier

router = APIRouter()

class RunRequest(BaseModel):
    flight_id: str
    delay_min: int

@router.post("/run")
def run_engine(
    req: RunRequest,
    company: Company = Depends(require_tier("pro")),  # ✅ paid endpoint
    db: Session = Depends(get_db),
):
    # Meter usage
    db.add(UsageEvent(company_id=company.id, event="run", quantity=1, meta_json=json.dumps(req.model_dump())))
    db.commit()

    # TODO: replace with your real simulation
    return {
        "company_id": company.id,
        "tier": company.tier,
        "result": {
            "status": "ok",
            "message": "Real SaaS endpoint: replace this with PIE engine output",
            "input": req.model_dump(),
        },
    }
