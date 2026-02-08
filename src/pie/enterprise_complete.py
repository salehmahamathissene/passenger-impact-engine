"""
COMPLETE PASSENGER IMPACT ENGINE - ENTERPRISE EDITION
INCLUDING: Companies, Contracts, Jobs, Invoices, Analytics
"""
from fastapi import FastAPI, HTTPException, Header, Depends, Query, BackgroundTasks, UploadFile, File, Form
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import uuid
import json
import csv
import io
from enum import Enum
import asyncio

# ==================== CONFIGURATION ====================
DATABASE_URL = "postgresql://pie:piepass@127.0.0.1:55432/pie_enterprise"
ENTERPRISE_ADMIN_KEY = "test_admin_key_123"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ==================== PYDANTIC MODELS ====================
class Tier(str, Enum):
    SMALL = "small"
    MID = "mid"
    LARGE = "large"

class Industry(str, Enum):
    AIRLINE = "airline"
    AIRPORT = "airport"
    GROUND_HANDLER = "ground_handler"
    OTHER = "other"

class ContractType(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CompanyCreate(BaseModel):
    legal_name: str = Field(..., min_length=1, max_length=255)
    trading_name: Optional[str] = Field(None, max_length=255)
    tier: Tier = Tier.MID
    industry: Industry = Industry.AIRLINE
    country: Optional[str] = Field(None, max_length=2)
    phone: Optional[str] = None
    support_email: Optional[str] = None
    billing_email: Optional[str] = None
    website: Optional[str] = None
    employee_count: Optional[int] = Field(None, gt=0)
    annual_revenue_eur: Optional[float] = Field(None, gt=0)

class ContractCreate(BaseModel):
    contract_type: ContractType = ContractType.STANDARD
    start_date: date
    end_date: date
    monthly_fee_eur: float = Field(..., gt=0)
    features: List[str] = ["basic_reporting", "api_access"]

class InvoiceItem(BaseModel):
    description: str
    quantity: int = 1
    unit_price_eur: float = Field(..., gt=0)

# ==================== DATABASE SCHEMA ====================
def init_database():
    """Initialize database with all required tables"""
    db = SessionLocal()
    try:
        # Create companies table if not exists
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS enterprise_companies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                legal_name VARCHAR(255) NOT NULL UNIQUE,
                trading_name VARCHAR(255),
                tier VARCHAR(50) NOT NULL CHECK (tier IN ('small', 'mid', 'large')),
                industry VARCHAR(50) NOT NULL CHECK (industry IN ('airline', 'airport', 'ground_handler', 'other')),
                country VARCHAR(2),
                phone VARCHAR(50),
                support_email VARCHAR(255),
                billing_email VARCHAR(255),
                website VARCHAR(255),
                employee_count INTEGER CHECK (employee_count > 0),
                annual_revenue_eur DECIMAL(15, 2),
                total_spent DECIMAL(15, 2) DEFAULT 0.00,
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE
            )
        """))
        
        # Create contracts table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS enterprise_contracts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                company_id UUID NOT NULL REFERENCES enterprise_companies(id) ON DELETE CASCADE,
                contract_type VARCHAR(50) NOT NULL CHECK (contract_type IN ('standard', 'premium', 'enterprise')),
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                monthly_fee_eur DECIMAL(15, 2) NOT NULL CHECK (monthly_fee_eur > 0),
                features JSONB DEFAULT '[]'::jsonb,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create jobs table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS enterprise_jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                company_id UUID NOT NULL REFERENCES enterprise_companies(id) ON DELETE CASCADE,
                job_type VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
                parameters JSONB DEFAULT '{}'::jsonb,
                result JSONB DEFAULT '{}'::jsonb,
                error_message TEXT,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create invoices table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS enterprise_invoices (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                company_id UUID NOT NULL REFERENCES enterprise_companies(id) ON DELETE CASCADE,
                invoice_number VARCHAR(100) UNIQUE NOT NULL,
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                total_amount_eur DECIMAL(15, 2) NOT NULL CHECK (total_amount_eur >= 0),
                items JSONB DEFAULT '[]'::jsonb,
                is_paid BOOLEAN DEFAULT FALSE,
                paid_at TIMESTAMP WITH TIME ZONE,
                due_date DATE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        db.commit()
        print("✅ Database tables initialized successfully")
    except Exception as e:
        db.rollback()
        print(f"❌ Database initialization failed: {e}")
    finally:
        db.close()

# ==================== DEPENDENCIES ====================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_admin_key(x_admin_key: str = Header(None)):
    if not x_admin_key:
        raise HTTPException(status_code=401, detail="Admin key required")
    if x_admin_key != ENTERPRISE_ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return x_admin_key

# ==================== FASTAPI APP ====================
app = FastAPI(
    title="Passenger Impact Engine - Enterprise API",
    description="Complete enterprise platform for passenger impact analysis",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()

# ==================== COMPANY ENDPOINTS ====================

@app.post("/enterprise/companies", status_code=201)
async def create_company(
    company: CompanyCreate,
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Create a new enterprise company"""
    try:
        # Check for duplicate
        check_sql = text("SELECT id FROM enterprise_companies WHERE legal_name = :legal_name")
        existing = db.execute(check_sql, {"legal_name": company.legal_name}).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="legal_name already exists")
        
        # Create company
        company_id = str(uuid.uuid4())
        now = datetime.now()
        
        insert_sql = text("""
            INSERT INTO enterprise_companies (
                id, created_at, updated_at,
                legal_name, trading_name, tier, industry, country,
                phone, support_email, billing_email, website,
                employee_count, annual_revenue_eur,
                is_active, is_verified, total_spent
            ) VALUES (
                :id, :created_at, :updated_at,
                :legal_name, :trading_name, :tier, :industry, :country,
                :phone, :support_email, :billing_email, :website,
                :employee_count, :annual_revenue_eur,
                TRUE, FALSE, 0.00
            )
            RETURNING id::text
        """)
        
        params = {
            "id": company_id,
            "created_at": now,
            "updated_at": now,
            "legal_name": company.legal_name,
            "trading_name": company.trading_name,
            "tier": company.tier.value,
            "industry": company.industry.value,
            "country": company.country,
            "phone": company.phone,
            "support_email": company.support_email,
            "billing_email": company.billing_email,
            "website": company.website,
            "employee_count": company.employee_count,
            "annual_revenue_eur": company.annual_revenue_eur
        }
        
        result = db.execute(insert_sql, params)
        db.commit()
        
        company_id = result.fetchone()[0]
        
        return {
            "message": "Company created successfully",
            "id": company_id,
            "legal_name": company.legal_name,
            "trading_name": company.trading_name,
            "tier": company.tier.value,
            "industry": company.industry.value,
            "country": company.country
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

@app.get("/enterprise/companies/{company_id}")
async def get_company(
    company_id: str,
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Get company details"""
    try:
        sql = text("""
            SELECT 
                id::text, 
                legal_name, 
                trading_name, 
                tier, 
                industry, 
                country, 
                phone, 
                support_email, 
                billing_email, 
                website,
                employee_count, 
                annual_revenue_eur, 
                is_active, 
                is_verified,
                total_spent,
                created_at
            FROM enterprise_companies 
            WHERE id = :company_id
        """)
        
        result = db.execute(sql, {"company_id": company_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return dict(row._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/enterprise/companies")
async def list_companies(
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all companies"""
    try:
        sql = text("""
            SELECT 
                id::text, 
                legal_name, 
                trading_name, 
                tier, 
                industry, 
                country, 
                phone, 
                support_email, 
                billing_email, 
                website,
                employee_count, 
                annual_revenue_eur, 
                is_active, 
                is_verified,
                total_spent,
                created_at
            FROM enterprise_companies 
            ORDER BY created_at DESC 
            LIMIT :limit OFFSET :skip
        """)
        
        result = db.execute(sql, {"limit": limit, "skip": skip})
        companies = [dict(row._mapping) for row in result]
        
        count_sql = text("SELECT COUNT(*) FROM enterprise_companies")
        total = db.execute(count_sql).scalar()
        
        return {
            "companies": companies,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== CONTRACT ENDPOINTS ====================

@app.post("/enterprise/companies/{company_id}/contracts", status_code=201)
async def create_contract(
    company_id: str,
    contract: ContractCreate,
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Create a contract for a company"""
    try:
        # Check if company exists
        company_sql = text("SELECT id FROM enterprise_companies WHERE id = :company_id")
        if not db.execute(company_sql, {"company_id": company_id}).fetchone():
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Check for existing active contract
        existing_sql = text("""
            SELECT id FROM enterprise_contracts 
            WHERE company_id = :company_id 
            AND is_active = TRUE 
            AND end_date >= CURRENT_DATE
        """)
        existing = db.execute(existing_sql, {"company_id": company_id}).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Active contract already exists")
        
        # Create contract
        contract_id = str(uuid.uuid4())
        now = datetime.now()
        
        insert_sql = text("""
            INSERT INTO enterprise_contracts (
                id, company_id, contract_type, start_date, end_date,
                monthly_fee_eur, features, is_active, created_at, updated_at
            ) VALUES (
                :id, :company_id, :contract_type, :start_date, :end_date,
                :monthly_fee_eur, :features, TRUE, :created_at, :updated_at
            )
            RETURNING id::text, contract_type, start_date, end_date, monthly_fee_eur
        """)
        
        params = {
            "id": contract_id,
            "company_id": company_id,
            "contract_type": contract.contract_type.value,
            "start_date": contract.start_date,
            "end_date": contract.end_date,
            "monthly_fee_eur": contract.monthly_fee_eur,
            "features": json.dumps(contract.features),
            "created_at": now,
            "updated_at": now
        }
        
        result = db.execute(insert_sql, params)
        db.commit()
        
        contract_data = dict(result.fetchone()._mapping)
        
        return {
            "message": "Contract created successfully",
            "contract": contract_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create contract: {str(e)}")

@app.get("/enterprise/companies/{company_id}/contracts")
async def get_company_contracts(
    company_id: str,
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Get all contracts for a company"""
    try:
        sql = text("""
            SELECT 
                id::text,
                contract_type,
                start_date,
                end_date,
                monthly_fee_eur,
                features,
                is_active,
                created_at
            FROM enterprise_contracts 
            WHERE company_id = :company_id
            ORDER BY created_at DESC
        """)
        
        result = db.execute(sql, {"company_id": company_id})
        contracts = [dict(row._mapping) for row in result]
        
        return {
            "company_id": company_id,
            "contracts": contracts,
            "count": len(contracts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== JOB ENDPOINTS ====================

@app.post("/enterprise/companies/{company_id}/jobs/upload")
async def upload_job_data(
    company_id: str,
    job_type: str = Form(...),
    schedule_file: UploadFile = File(None),
    bookings_file: UploadFile = File(None),
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Upload data files and create a processing job"""
    try:
        # Check if company exists
        company_sql = text("SELECT id FROM enterprise_companies WHERE id = :company_id")
        if not db.execute(company_sql, {"company_id": company_id}).fetchone():
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Read and parse files
        parameters = {"job_type": job_type}
        
        if schedule_file:
            content = await schedule_file.read()
            schedule_data = content.decode('utf-8')
            parameters["schedule_rows"] = len(schedule_data.splitlines()) - 1  # Exclude header
        
        if bookings_file:
            content = await bookings_file.read()
            bookings_data = content.decode('utf-8')
            parameters["bookings_rows"] = len(bookings_data.splitlines()) - 1
        
        # Create job
        job_id = str(uuid.uuid4())
        now = datetime.now()
        
        insert_sql = text("""
            INSERT INTO enterprise_jobs (
                id, company_id, job_type, status, parameters,
                created_at
            ) VALUES (
                :id, :company_id, :job_type, 'pending', :parameters,
                :created_at
            )
            RETURNING id::text, job_type, status, created_at
        """)
        
        params = {
            "id": job_id,
            "company_id": company_id,
            "job_type": job_type,
            "parameters": json.dumps(parameters),
            "created_at": now
        }
        
        result = db.execute(insert_sql, params)
        db.commit()
        
        job_data = dict(result.fetchone()._mapping)
        
        # Simulate background processing
        asyncio.create_task(process_job_background(job_id, db))
        
        return {
            "message": "Job created and queued for processing",
            "job_id": job_id,
            "job": job_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

async def process_job_background(job_id: str, db):
    """Background task to process job"""
    try:
        # Update job status to processing
        update_sql = text("""
            UPDATE enterprise_jobs 
            SET status = 'processing', started_at = :started_at
            WHERE id = :job_id
        """)
        db.execute(update_sql, {"job_id": job_id, "started_at": datetime.now()})
        db.commit()
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Generate fake results
        results = {
            "total_flights": 150,
            "total_passengers": 12500,
            "total_revenue_eur": 2500000,
            "average_load_factor": 0.85,
            "processed_at": datetime.now().isoformat()
        }
        
        # Update job as completed
        complete_sql = text("""
            UPDATE enterprise_jobs 
            SET status = 'completed', result = :result, completed_at = :completed_at
            WHERE id = :job_id
        """)
        db.execute(complete_sql, {
            "job_id": job_id,
            "result": json.dumps(results),
            "completed_at": datetime.now()
        })
        db.commit()
        
    except Exception as e:
        # Mark job as failed
        error_sql = text("""
            UPDATE enterprise_jobs 
            SET status = 'failed', error_message = :error, completed_at = :completed_at
            WHERE id = :job_id
        """)
        db.execute(error_sql, {
            "job_id": job_id,
            "error": str(e),
            "completed_at": datetime.now()
        })
        db.commit()

@app.post("/enterprise/jobs/{job_id}/run")
async def run_job(
    job_id: str,
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Manually trigger job processing"""
    try:
        # Check if job exists
        job_sql = text("SELECT id, status FROM enterprise_jobs WHERE id = :job_id")
        job = db.execute(job_sql, {"job_id": job_id}).fetchone()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status == 'processing':
            raise HTTPException(status_code=400, detail="Job is already processing")
        
        # Start background processing
        asyncio.create_task(process_job_background(job_id, db))
        
        return {
            "message": "Job processing started",
            "job_id": job_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run job: {str(e)}")

@app.get("/enterprise/jobs/{job_id}")
async def get_job(
    job_id: str,
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Get job details and results"""
    try:
        sql = text("""
            SELECT 
                id::text,
                company_id::text,
                job_type,
                status,
                parameters,
                result,
                error_message,
                started_at,
                completed_at,
                created_at
            FROM enterprise_jobs 
            WHERE id = :job_id
        """)
        
        result = db.execute(sql, {"job_id": job_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = dict(row._mapping)
        
        # Parse JSON fields
        if job_data.get('parameters'):
            job_data['parameters'] = json.loads(job_data['parameters'])
        if job_data.get('result'):
            job_data['result'] = json.loads(job_data['result'])
        
        return job_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/enterprise/jobs")
async def list_jobs(
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db),
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all jobs with filtering"""
    try:
        where_clauses = []
        params = {"skip": skip, "limit": limit}
        
        if company_id:
            where_clauses.append("company_id = :company_id")
            params["company_id"] = company_id
        
        if status:
            where_clauses.append("status = :status")
            params["status"] = status
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        sql = text(f"""
            SELECT 
                id::text,
                company_id::text,
                job_type,
                status,
                created_at
            FROM enterprise_jobs 
            {where_sql}
            ORDER BY created_at DESC 
            LIMIT :limit OFFSET :skip
        """)
        
        result = db.execute(sql, params)
        jobs = [dict(row._mapping) for row in result]
        
        count_sql = text(f"SELECT COUNT(*) FROM enterprise_jobs {where_sql}")
        total = db.execute(count_sql, params).scalar()
        
        return {
            "jobs": jobs,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== INVOICE ENDPOINTS ====================

@app.post("/enterprise/companies/{company_id}/invoices/generate")
async def generate_invoice(
    company_id: str,
    period_start: date,
    period_end: date,
    items: List[InvoiceItem],
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Generate an invoice for a company"""
    try:
        # Check if company exists
        company_sql = text("SELECT id, legal_name FROM enterprise_companies WHERE id = :company_id")
        company = db.execute(company_sql, {"company_id": company_id}).fetchone()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Calculate total
        total_amount = sum(item.quantity * item.unit_price_eur for item in items)
        
        # Generate invoice number
        invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Create invoice
        invoice_id = str(uuid.uuid4())
        now = datetime.now()
        due_date = now + timedelta(days=30)
        
        # Convert items to JSON
        items_json = [item.dict() for item in items]
        
        insert_sql = text("""
            INSERT INTO enterprise_invoices (
                id, company_id, invoice_number, period_start, period_end,
                total_amount_eur, items, is_paid, due_date, created_at
            ) VALUES (
                :id, :company_id, :invoice_number, :period_start, :period_end,
                :total_amount_eur, :items, FALSE, :due_date, :created_at
            )
            RETURNING id::text, invoice_number, total_amount_eur, due_date
        """)
        
        params = {
            "id": invoice_id,
            "company_id": company_id,
            "invoice_number": invoice_number,
            "period_start": period_start,
            "period_end": period_end,
            "total_amount_eur": total_amount,
            "items": json.dumps(items_json),
            "due_date": due_date.date(),
            "created_at": now
        }
        
        result = db.execute(insert_sql, params)
        db.commit()
        
        invoice_data = dict(result.fetchone()._mapping)
        
        return {
            "message": "Invoice generated successfully",
            "invoice": invoice_data,
            "company": dict(company._mapping)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate invoice: {str(e)}")

@app.get("/enterprise/companies/{company_id}/invoices")
async def get_company_invoices(
    company_id: str,
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db),
    paid_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all invoices for a company"""
    try:
        where_clauses = ["company_id = :company_id"]
        params = {"company_id": company_id, "skip": skip, "limit": limit}
        
        if paid_only:
            where_clauses.append("is_paid = TRUE")
        
        where_sql = "WHERE " + " AND ".join(where_clauses)
        
        sql = text(f"""
            SELECT 
                id::text,
                invoice_number,
                period_start,
                period_end,
                total_amount_eur,
                items,
                is_paid,
                paid_at,
                due_date,
                created_at
            FROM enterprise_invoices 
            {where_sql}
            ORDER BY created_at DESC 
            LIMIT :limit OFFSET :skip
        """)
        
        result = db.execute(sql, params)
        invoices = []
        
        for row in result:
            invoice_data = dict(row._mapping)
            if invoice_data.get('items'):
                invoice_data['items'] = json.loads(invoice_data['items'])
            invoices.append(invoice_data)
        
        # Get company info
        company_sql = text("SELECT legal_name, trading_name FROM enterprise_companies WHERE id = :company_id")
        company = db.execute(company_sql, {"company_id": company_id}).fetchone()
        
        # Get summary
        summary_sql = text("""
            SELECT 
                COUNT(*) as total_invoices,
                SUM(CASE WHEN is_paid THEN total_amount_eur ELSE 0 END) as paid_amount,
                SUM(CASE WHEN NOT is_paid AND due_date < CURRENT_DATE THEN total_amount_eur ELSE 0 END) as overdue_amount,
                SUM(CASE WHEN NOT is_paid AND due_date >= CURRENT_DATE THEN total_amount_eur ELSE 0 END) as pending_amount
            FROM enterprise_invoices 
            WHERE company_id = :company_id
        """)
        summary = db.execute(summary_sql, {"company_id": company_id}).fetchone()
        
        return {
            "company": dict(company._mapping) if company else {},
            "invoices": invoices,
            "summary": dict(summary._mapping) if summary else {},
            "pagination": {
                "skip": skip,
                "limit": limit,
                "count": len(invoices)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/enterprise/analytics/summary")
async def get_analytics_summary(
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Get comprehensive analytics summary"""
    try:
        # Company statistics
        companies_sql = text("""
            SELECT 
                COUNT(*) as total_companies,
                SUM(CASE WHEN tier = 'small' THEN 1 ELSE 0 END) as small_companies,
                SUM(CASE WHEN tier = 'mid' THEN 1 ELSE 0 END) as mid_companies,
                SUM(CASE WHEN tier = 'large' THEN 1 ELSE 0 END) as large_companies,
                COUNT(DISTINCT industry) as industries_covered,
                COUNT(DISTINCT country) as countries
            FROM enterprise_companies 
            WHERE is_active = TRUE
        """)
        companies_stats = db.execute(companies_sql).fetchone()
        
        # Contract statistics
        contracts_sql = text("""
            SELECT 
                COUNT(*) as total_contracts,
                SUM(CASE WHEN contract_type = 'standard' THEN 1 ELSE 0 END) as standard_contracts,
                SUM(CASE WHEN contract_type = 'premium' THEN 1 ELSE 0 END) as premium_contracts,
                SUM(CASE WHEN contract_type = 'enterprise' THEN 1 ELSE 0 END) as enterprise_contracts,
                AVG(monthly_fee_eur) as avg_monthly_fee
            FROM enterprise_contracts 
            WHERE is_active = TRUE
        """)
        contracts_stats = db.execute(contracts_sql).fetchone()
        
        # Job statistics
        jobs_sql = text("""
            SELECT 
                COUNT(*) as total_jobs,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
                SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing_jobs,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs
            FROM enterprise_jobs
        """)
        jobs_stats = db.execute(jobs_sql).fetchone()
        
        # Revenue statistics
        revenue_sql = text("""
            SELECT 
                COALESCE(SUM(total_amount_eur), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN is_paid THEN total_amount_eur ELSE 0 END), 0) as paid_revenue,
                COALESCE(AVG(total_amount_eur), 0) as avg_invoice_amount
            FROM enterprise_invoices
        """)
        revenue_stats = db.execute(revenue_sql).fetchone()
        
        return {
            "companies": dict(companies_stats._mapping) if companies_stats else {},
            "contracts": dict(contracts_stats._mapping) if contracts_stats else {},
            "jobs": dict(jobs_stats._mapping) if jobs_stats else {},
            "revenue": dict(revenue_stats._mapping) if revenue_stats else {},
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

# ==================== HEALTH ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "message": "Passenger Impact Engine - Enterprise API",
        "version": "3.0.0",
        "status": "operational",
        "endpoints": {
            "companies": "/enterprise/companies",
            "contracts": "/enterprise/companies/{id}/contracts",
            "jobs": "/enterprise/jobs",
            "invoices": "/enterprise/companies/{id}/invoices",
            "analytics": "/enterprise/analytics/summary",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/enterprise/health")
async def enterprise_health(
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Enterprise health check"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        # Get counts
        counts_sql = text("""
            SELECT 
                (SELECT COUNT(*) FROM enterprise_companies) as companies,
                (SELECT COUNT(*) FROM enterprise_contracts) as contracts,
                (SELECT COUNT(*) FROM enterprise_jobs) as jobs,
                (SELECT COUNT(*) FROM enterprise_invoices) as invoices
        """)
        counts = db.execute(counts_sql).fetchone()
        
        return {
            "status": "healthy",
            "database": "connected",
            "services": "operational",
            "counts": dict(counts._mapping) if counts else {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
