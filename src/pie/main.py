from __future__ import annotations

import os
import uuid
from datetime import datetime, date
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File, Form
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Import billing module
try:
    from .stripe_integration import router as billing_router
    HAS_BILLING = True
except ImportError:
    HAS_BILLING = False
    print("Warning: Billing module not available")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pie:piepass@127.0.0.1:55432/pie_enterprise")
ENTERPRISE_ADMIN_KEY = os.getenv("ENTERPRISE_ADMIN_KEY", "test_admin_key_123")
LOCAL_BLOB_DIR = os.getenv("LOCAL_BLOB_DIR", "blob")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_admin_key(x_admin_key: str | None):
    if not x_admin_key:
        raise HTTPException(status_code=401, detail="Admin key required")
    if x_admin_key != ENTERPRISE_ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")

ALLOWED_INDUSTRIES = {"airline", "airport", "ground_handler", "other"}
ALLOWED_TIERS = {"small", "mid", "large"}

def normalize_tier(tier_value):
    tier_map = {"small": "small", "medium": "mid", "mid": "mid", "large": "large"}
    if tier_value is None:
        return "small"
    t = str(tier_value).lower()
    if t not in tier_map:
        raise HTTPException(status_code=422, detail={"field": "tier", "allowed": sorted(ALLOWED_TIERS), "got": tier_value})
    return tier_map[t]

def validate_industry(industry_value):
    ind = (industry_value or "").strip().lower()
    if ind not in ALLOWED_INDUSTRIES:
        raise HTTPException(status_code=422, detail={"field": "industry", "allowed": sorted(ALLOWED_INDUSTRIES), "got": ind})
    return ind

def put_bytes(path: str, data: bytes) -> str:
    os.makedirs(os.path.join(LOCAL_BLOB_DIR, os.path.dirname(path)), exist_ok=True)
    full = os.path.join(LOCAL_BLOB_DIR, path)
    with open(full, "wb") as f:
        f.write(data)
    return f"local://{path}"

app = FastAPI(
    title="Passenger Impact Engine",
    version="2.0.0",
    description="SaaS Platform for Airline Disruption Analysis"
)

# Include billing routes if available
if HAS_BILLING:
    app.include_router(billing_router)
    print("✅ Billing module loaded")
else:
    print("⚠️  Billing module not loaded")

@app.get("/")
def root():
    return {
        "service": "Passenger Impact Engine",
        "version": "2.0.0",
        "status": "operational",
        "has_billing": HAS_BILLING,
        "endpoints": {
            "health": "/health",
            "enterprise": "/enterprise/*",
            "billing": "/billing/*" if HAS_BILLING else "not_available"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/enterprise/health")
def ent_health(x_admin_key: str | None = Header(None), db=Depends(get_db)):
    verify_admin_key(x_admin_key)
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "billing_enabled": HAS_BILLING}

@app.post("/enterprise/companies")
def create_company(
    legal_name: str = Form(...),
    trading_name: Optional[str] = Form(None),
    tier: str = Form("mid"),
    industry: str = Form("airline"),
    country: str = Form("US"),
    x_admin_key: str | None = Header(None),
    db=Depends(get_db)
):
    verify_admin_key(x_admin_key)

    tier = normalize_tier(tier)
    industry = validate_industry(industry)

    company_id = str(uuid.uuid4())
    now = datetime.utcnow()

    sql = text("""
        INSERT INTO enterprise_companies (
            id, created_at, updated_at,
            legal_name, trading_name, tier, industry, country,
            is_active, is_verified, total_spent
        ) VALUES (
            :id, :created_at, :updated_at,
            :legal_name, :trading_name, :tier, :industry, :country,
            TRUE, FALSE, 0.00
        )
        RETURNING id::text, legal_name, trading_name, tier, industry, country, created_at
    """)

    try:
        row = db.execute(sql, {
            "id": company_id,
            "created_at": now,
            "updated_at": now,
            "legal_name": legal_name,
            "trading_name": trading_name,
            "tier": tier,
            "industry": industry,
            "country": country,
        }).fetchone()
        db.commit()
        return {"message": "Company created successfully", **dict(row._mapping)}
    except IntegrityError as e:
        db.rollback()
        msg = str(getattr(e, "orig", e))
        if "enterprise_companies_legal_name_key" in msg or "UniqueViolation" in msg:
            raise HTTPException(status_code=409, detail="legal_name already exists")
        raise HTTPException(status_code=400, detail="Integrity error")

@app.get("/enterprise/companies")
def list_companies(x_admin_key: str | None = Header(None), db=Depends(get_db)):
    verify_admin_key(x_admin_key)
    
    rows = db.execute(text("""
        SELECT id::text, legal_name, trading_name, tier, industry, country, created_at
        FROM enterprise_companies
        ORDER BY created_at DESC
    """)).fetchall()
    
    return {"companies": [dict(row._mapping) for row in rows]}

@app.post("/enterprise/companies/{company_id}/contracts")
def create_contract(
    company_id: str,
    plan: str = Form("starter"),
    starts_at: Optional[str] = Form(None),
    ends_at: Optional[str] = Form(None),
    x_admin_key: str | None = Header(None),
    db=Depends(get_db)
):
    verify_admin_key(x_admin_key)

    plan = plan.lower()
    if plan not in {"starter", "pro", "enterprise"}:
        raise HTTPException(status_code=422, detail={"field":"plan","allowed":["starter","pro","enterprise"],"got":plan})

    exists = db.execute(text("SELECT 1 FROM enterprise_companies WHERE id = :id"), {"id": company_id}).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="Company not found")

    contract_id = str(uuid.uuid4())
    contract_number = f"CT-{datetime.utcnow().strftime('%Y%m%d')}-{contract_id[:8].upper()}"

    row = db.execute(text("""
        INSERT INTO enterprise_contracts (
            id, company_id, contract_number, plan, signed_at, starts_at, ends_at, status
        ) VALUES (
            :id, :company_id, :contract_number, :plan, :signed_at, :starts_at, :ends_at, 'active'
        )
        RETURNING id::text, contract_number, plan, status, starts_at, ends_at
    """), {
        "id": contract_id,
        "company_id": company_id,
        "contract_number": contract_number,
        "plan": plan,
        "signed_at": datetime.utcnow(),
        "starts_at": starts_at or date.today().isoformat(),
        "ends_at": ends_at,
    }).fetchone()
    db.commit()
    return {"message": "Contract created", "contract": dict(row._mapping)}

@app.post("/enterprise/companies/{company_id}/jobs")
def create_job(company_id: str, x_admin_key: str | None = Header(None), db=Depends(get_db)):
    verify_admin_key(x_admin_key)

    exists = db.execute(text("SELECT 1 FROM enterprise_companies WHERE id = :id"), {"id": company_id}).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail="Company not found")

    job_id = str(uuid.uuid4())
    outputs_prefix = f"outputs/{company_id}/{job_id}"

    row = db.execute(text("""
        INSERT INTO enterprise_jobs (id, company_id, status, created_at, outputs_prefix)
        VALUES (:id, :company_id, 'queued', NOW(), :outputs_prefix)
        RETURNING id::text, company_id::text, status, created_at, outputs_prefix
    """), {"id": job_id, "company_id": company_id, "outputs_prefix": outputs_prefix}).fetchone()
    db.commit()
    return {"message": "Job created", "job": dict(row._mapping)}

@app.post("/enterprise/jobs/{job_id}/upload/schedule")
async def upload_schedule(job_id: str, file: UploadFile = File(...), x_admin_key: str | None = Header(None), db=Depends(get_db)):
    verify_admin_key(x_admin_key)
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="CSV required")

    job = db.execute(text("SELECT id, company_id FROM enterprise_jobs WHERE id = :id"), {"id": job_id}).fetchone()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    data = await file.read()
    company_id = str(job._mapping["company_id"])
    stored = put_bytes(f"uploads/{company_id}/{job_id}/schedule.csv", data)

    db.execute(text("UPDATE enterprise_jobs SET schedule_blob_path = :p WHERE id = :id"), {"p": stored, "id": job_id})
    db.commit()
    return {"message": "Schedule uploaded", "path": stored}

@app.post("/enterprise/jobs/{job_id}/upload/bookings")
async def upload_bookings(job_id: str, file: UploadFile = File(...), x_admin_key: str | None = Header(None), db=Depends(get_db)):
    verify_admin_key(x_admin_key)
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="CSV required")

    job = db.execute(text("SELECT id, company_id FROM enterprise_jobs WHERE id = :id"), {"id": job_id}).fetchone()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    data = await file.read()
    company_id = str(job._mapping["company_id"])
    stored = put_bytes(f"uploads/{company_id}/{job_id}/bookings.csv", data)

    db.execute(text("UPDATE enterprise_jobs SET bookings_blob_path = :p WHERE id = :id"), {"p": stored, "id": job_id})
    db.commit()
    return {"message": "Bookings uploaded", "path": stored}

@app.get("/enterprise/jobs/{job_id}")
def get_job(job_id: str, x_admin_key: str | None = Header(None), db=Depends(get_db)):
    verify_admin_key(x_admin_key)
    row = db.execute(text("""
        SELECT id::text, company_id::text, status, created_at, started_at, finished_at,
               schedule_blob_path, bookings_blob_path, outputs_prefix, error_message
        FROM enterprise_jobs
        WHERE id = :id
    """), {"id": job_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(row._mapping)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ----------------------------
# Render Health Check Support
# ----------------------------
@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "passenger-impact-engine"}

