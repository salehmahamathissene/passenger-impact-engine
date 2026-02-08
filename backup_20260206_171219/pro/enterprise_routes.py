from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .settings import settings
from .db import get_db
from .enterprise_models import (
    EnterpriseCompany, EnterpriseContract, EnterpriseInvoice, EnterpriseOrder, EnterpriseJob,
    CompanyTier, IndustryType, ContractStatus, InvoiceStatus, JobStatus
)
from .queue import enqueue_enterprise_job

router = APIRouter(prefix="/enterprise", tags=["enterprise"])


# ------------------ Security ------------------
def _hash_key(raw: str) -> str:
    # stable hash (store in DB). In real life: use bcrypt/argon2.
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def require_admin(x_admin_key: str = Header(default="", alias="X-Admin-Key")) -> str:
    expected = (settings.ENTERPRISE_ADMIN_KEY or "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="ENTERPRISE_ADMIN_KEY not set")
    if not hmac.compare_digest(x_admin_key.strip(), expected):
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return x_admin_key


def require_company(company_id: str = Header(default="", alias="X-Company-Id"),
                    x_api_key: str = Header(default="", alias="X-Api-Key"),
                    db: Session = Depends(get_db)) -> EnterpriseCompany:
    try:
        cid = uuid.UUID(company_id.strip())
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid X-Company-Id")

    c = db.get(EnterpriseCompany, cid)
    if not c or not c.is_active:
        raise HTTPException(status_code=401, detail="Company not found or inactive")

    if not c.api_key_hash:
        raise HTTPException(status_code=401, detail="Company API key not provisioned")

    if not hmac.compare_digest(_hash_key(x_api_key.strip()), c.api_key_hash):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return c


# ------------------ Schemas ------------------
class CompanyCreate(BaseModel):
    legal_name: str = Field(..., min_length=2, max_length=200)
    trading_name: Optional[str] = Field(None, max_length=200)
    tier: CompanyTier = CompanyTier.small
    industry: IndustryType = IndustryType.airline
    country: Optional[str] = Field(None, max_length=100)
    support_email: Optional[EmailStr] = None


class ContractCreate(BaseModel):
    monthly_allowance_runs: int = Field(100000, ge=1000, le=10_000_000)
    max_concurrent_jobs: int = Field(5, ge=1, le=200)
    monthly_fee_eur: Decimal = Field(Decimal("0.00"), ge=0)
    currency: str = Field("EUR", min_length=3, max_length=3)


class InvoiceCreate(BaseModel):
    company_id: uuid.UUID
    subtotal_eur: Decimal = Field(..., gt=0)
    tax_eur: Decimal = Field(Decimal("0.00"), ge=0)
    due_days: int = Field(30, ge=1, le=120)
    notes: Optional[str] = None


class OrderCreate(BaseModel):
    description: str = Field(..., min_length=5, max_length=500)
    iterations: int = Field(..., gt=0, le=1_000_000)


class InvoiceSettle(BaseModel):
    payment_reference: str = Field(..., min_length=3, max_length=200)


# ------------------ Endpoints ------------------
@router.get("/health")
def health(db: Session = Depends(get_db), _admin: str = Depends(require_admin)):
    # Admin-only health (enterprise surface)
    companies = db.query(EnterpriseCompany).count()
    invoices = db.query(EnterpriseInvoice).count()
    orders = db.query(EnterpriseOrder).count()
    return {
        "status": "healthy",
        "database": "connected",
        "entities": {"companies": companies, "invoices": invoices, "orders": orders},
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/companies")
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), _admin: str = Depends(require_admin)):
    exists = db.query(EnterpriseCompany).filter(EnterpriseCompany.legal_name == payload.legal_name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Company already exists")

    c = EnterpriseCompany(
        legal_name=payload.legal_name,
        trading_name=payload.trading_name,
        tier=payload.tier,
        industry=payload.industry,
        country=payload.country,
        support_email=str(payload.support_email) if payload.support_email else None,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"company_id": str(c.id), "legal_name": c.legal_name}


@router.post("/companies/{company_id}/provision-api-key")
def provision_company_key(company_id: uuid.UUID, db: Session = Depends(get_db), _admin: str = Depends(require_admin)):
    c = db.get(EnterpriseCompany, company_id)
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")
    raw = secrets.token_urlsafe(48)
    c.api_key_hash = _hash_key(raw)
    c.updated_at = datetime.utcnow()
    db.commit()
    return {
        "company_id": str(c.id),
        "api_key": raw,  # shown ONCE (store it securely)
        "instructions": "Use headers: X-Company-Id + X-Api-Key",
    }


@router.post("/companies/{company_id}/contracts")
def create_contract(company_id: uuid.UUID, payload: ContractCreate, db: Session = Depends(get_db), _admin: str = Depends(require_admin)):
    c = db.get(EnterpriseCompany, company_id)
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")

    contract = EnterpriseContract(
        company_id=c.id,
        status=ContractStatus.active,
        monthly_allowance_runs=payload.monthly_allowance_runs,
        max_concurrent_jobs=payload.max_concurrent_jobs,
        monthly_fee_eur=payload.monthly_fee_eur,
        currency=payload.currency.upper(),
        start_date=datetime.utcnow(),
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return {"contract_id": str(contract.id), "status": contract.status.value}


@router.post("/invoices")
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db), _admin: str = Depends(require_admin)):
    c = db.get(EnterpriseCompany, payload.company_id)
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")

    inv_no = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
    due = datetime.utcnow() + timedelta(days=int(payload.due_days))
    total = payload.subtotal_eur + payload.tax_eur

    inv = EnterpriseInvoice(
        company_id=c.id,
        invoice_number=inv_no,
        status=InvoiceStatus.issued,
        subtotal_eur=payload.subtotal_eur,
        tax_eur=payload.tax_eur,
        total_eur=total,
        issued_at=datetime.utcnow(),
        due_at=due,
        notes=payload.notes,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return {"invoice_id": str(inv.id), "invoice_number": inv.invoice_number, "status": inv.status.value, "total_eur": str(inv.total_eur)}


@router.post("/orders")
def create_order(payload: OrderCreate, company: EnterpriseCompany = Depends(require_company), db: Session = Depends(get_db)):
    # Enterprise rule: you can create order anytime, but it will not execute until paid (invoice settlement)
    o = EnterpriseOrder(
        company_id=company.id,
        description=payload.description,
        iterations=payload.iterations,
        is_paid=False,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return {"order_id": str(o.id), "paid": o.is_paid}


@router.post("/invoices/{invoice_id}/settle")
def settle_invoice(invoice_id: uuid.UUID, payload: InvoiceSettle, db: Session = Depends(get_db), _admin: str = Depends(require_admin)):
    inv = db.get(EnterpriseInvoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv.status == InvoiceStatus.paid:
        return {"status": "already_paid", "invoice_number": inv.invoice_number}

    inv.status = InvoiceStatus.paid
    inv.paid_at = datetime.utcnow()
    inv.payment_reference = payload.payment_reference
    db.commit()

    return {"status": "paid", "invoice_number": inv.invoice_number, "paid_at": inv.paid_at.isoformat()}


@router.post("/orders/{order_id}/execute")
def execute_order(order_id: uuid.UUID, company: EnterpriseCompany = Depends(require_company), db: Session = Depends(get_db)):
    o = db.get(EnterpriseOrder, order_id)
    if not o or o.company_id != company.id:
        raise HTTPException(status_code=404, detail="Order not found")

    if not o.is_paid:
        raise HTTPException(status_code=402, detail="Order not paid (settle invoice first)")

    # Ensure job exists
    job = db.query(EnterpriseJob).filter(EnterpriseJob.order_id == o.id).first()
    if not job:
        job = EnterpriseJob(order_id=o.id, status=JobStatus.queued)
        db.add(job)
        db.commit()
        db.refresh(job)

    enqueue_enterprise_job(str(job.id))
    return {"job_id": str(job.id), "status": job.status.value}


@router.get("/jobs")
def list_jobs(company: EnterpriseCompany = Depends(require_company), db: Session = Depends(get_db)):
    # list by joining orders
    jobs = (
        db.query(EnterpriseJob, EnterpriseOrder)
        .join(EnterpriseOrder, EnterpriseJob.order_id == EnterpriseOrder.id)
        .filter(EnterpriseOrder.company_id == company.id)
        .order_by(desc(EnterpriseJob.started_at.nullslast()), desc(EnterpriseJob.finished_at.nullslast()))
        .limit(50)
        .all()
    )
    out = []
    for j, o in jobs:
        out.append({
            "job_id": str(j.id),
            "order_id": str(o.id),
            "status": j.status.value,
            "artifact_path": j.artifact_path,
            "error": j.error,
        })
    return out
