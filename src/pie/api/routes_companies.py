from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from pie.db import get_db
from pie.models import Company

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("")
def create_company(
    legal_name: str,
    trading_name: str = "",
    db: Session = Depends(get_db),
):
    c = Company(
        legal_name=legal_name,
        trading_name=trading_name,
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    return {"id": c.id, "legal_name": c.legal_name}
