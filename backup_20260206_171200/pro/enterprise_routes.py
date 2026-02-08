from __future__ import annotations

import uuid
import stripe
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr, validator, constr
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_, and_

from .settings import settings
from .db import get_db
from .enterprise_models import (
    EnterpriseCompany, EnterpriseContact, EnterpriseContract, 
    EnterpriseOrder, EnterpriseInvoice, EnterpriseJob,
    CompanyTier, IndustryType, SubscriptionPlan, 
    BillingCycle, PaymentMethod, ContractStatus
)
from .queue import enqueue_enterprise_job

router = APIRouter(prefix="/enterprise", tags=["enterprise"])

security = HTTPBearer()


# ==================== PYDANTIC MODELS ====================
class CompanyCreate(BaseModel):
    legal_name: str = Field(..., min_length=2, max_length=200)
    trading_name: Optional[str] = Field(None, max_length=200)
    company_number: Optional[str] = Field(None, max_length=50)
    vat_number: Optional[str] = Field(None, max_length=50)
    tier: CompanyTier = CompanyTier.SMALL
    industry: IndustryType = IndustryType.AIRLINE
    website: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    support_email: Optional[EmailStr] = None
    billing_email: Optional[EmailStr] = None
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[int] = Field(None, ge=1)
    annual_revenue_eur: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    legal_name: str
    trading_name: Optional[str]
    tier: CompanyTier
    industry: IndustryType
    website: Optional[str]
    phone: Optional[str]
    support_email: Optional[str]
    country: Optional[str]
    employee_count: Optional[int]
    is_active: bool
    is_verified: bool
    total_spent: Decimal
    created_at: datetime
    updated_at: datetime


class ContactCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    is_primary: bool = False
    is_technical: bool = False
    is_billing: bool = False
    can_receive_emails: bool = True
    can_receive_sms: bool = False


class ContractCreate(BaseModel):
    plan: SubscriptionPlan
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    monthly_rate_eur: Decimal = Field(..., gt=0)
    setup_fee_eur: Decimal = Field(0, ge=0)
    discount_percentage: Decimal = Field(0, ge=0, le=100)
    start_date: datetime
    end_date: Optional[datetime] = None
    auto_renew: bool = True
    renewal_notice_days: int = Field(30, ge=1, le=90)
    max_monthly_simulations: int = Field(..., gt=0)
    max_concurrent_jobs: int = Field(5, ge=1, le=100)
    priority_support: bool = False
    dedicated_account_manager: bool = False
    sla_response_time_hours: int = Field(48, ge=1, le=168)
    sla_uptime_percentage: Decimal = Field(Decimal('99.5'), ge=95, le=100)


class OrderCreate(BaseModel):
    description: str = Field(..., min_length=5, max_length=500)
    simulation_type: str = Field(..., min_length=2, max_length=100)
    iterations: int = Field(..., gt=0, le=1000000)
    priority: int = Field(5, ge=1, le=10)
    amount_eur: Decimal = Field(..., gt=0)
    currency: str = Field("EUR", min_length=3, max_length=3)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class InvoiceCreate(BaseModel):
    invoice_date: datetime
    due_date: datetime
    subtotal_eur: Decimal = Field(..., gt=0)
    tax_rate: Decimal = Field(..., ge=0, le=100)
    tax_number: Optional[str] = None
    line_items: List[Dict[str, Any]]
    notes: Optional[str] = None


# ==================== AUTHENTICATION ====================
def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for enterprise endpoints"""
    expected_key = settings.ENTERPRISE_API_KEY or "enterprise_demo_key"
    if credentials.credentials != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials


# ==================== COMPANY ENDPOINTS ====================
@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Create a new enterprise company"""
    
    # Check if company already exists
    existing = db.query(EnterpriseCompany).filter(
        or_(
            EnterpriseCompany.legal_name == company.legal_name,
            EnterpriseCompany.company_number == company.company_number
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company already exists"
        )
    
    # Create company
    db_company = EnterpriseCompany(
        **company.dict(exclude_none=True)
    )
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    return db_company


@router.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: uuid.UUID,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get company details"""
    company = db.get(EnterpriseCompany, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company


@router.get("/companies", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tier: Optional[CompanyTier] = None,
    industry: Optional[IndustryType] = None,
    country: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """List companies with filters"""
    query = db.query(EnterpriseCompany)
    
    if tier:
        query = query.filter(EnterpriseCompany.tier == tier)
    if industry:
        query = query.filter(EnterpriseCompany.industry == industry)
    if country:
        query = query.filter(EnterpriseCompany.country == country)
    if active_only:
        query = query.filter(EnterpriseCompany.is_active == True)
    
    companies = query.order_by(desc(EnterpriseCompany.created_at)).offset(skip).limit(limit).all()
    return companies


@router.post("/companies/{company_id}/contacts", response_model=dict)
async def create_contact(
    company_id: uuid.UUID,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Add contact to company"""
    company = db.get(EnterpriseCompany, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check for existing contact with same email
    existing = db.query(EnterpriseContact).filter(
        EnterpriseContact.company_id == company_id,
        EnterpriseContact.email == contact.email
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with this email already exists"
        )
    
    # Create contact
    db_contact = EnterpriseContact(
        company_id=company_id,
        **contact.dict(exclude_none=True)
    )
    
    db.add(db_contact)
    db.commit()
    
    return {
        "message": "Contact created successfully",
        "contact_id": db_contact.id,
        "company_id": company_id
    }


# ==================== CONTRACT ENDPOINTS ====================
@router.post("/companies/{company_id}/contracts", response_model=dict)
async def create_contract(
    company_id: uuid.UUID,
    contract: ContractCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Create enterprise contract"""
    company = db.get(EnterpriseCompany, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Generate contract number
    contract_number = f"CONT-{datetime.utcnow().year}-{str(uuid.uuid4())[:8].upper()}"
    
    # Calculate total amount
    monthly_rate = contract.monthly_rate_eur
    if contract.discount_percentage > 0:
        discount = monthly_rate * (contract.discount_percentage / 100)
        monthly_rate = monthly_rate - discount
    
    annual_rate = monthly_rate * 12 if contract.billing_cycle == BillingCycle.YEARLY else None
    
    # Create contract
    db_contract = EnterpriseContract(
        company_id=company_id,
        contract_number=contract_number,
        **contract.dict(exclude_none=True),
        monthly_rate_eur=monthly_rate,
        annual_rate_eur=annual_rate,
        status=ContractStatus.DRAFT
    )
    
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    
    # Update company tier if needed
    if contract.plan in [SubscriptionPlan.ENTERPRISE, SubscriptionPlan.CUSTOM]:
        company.tier = CompanyTier.ENTERPRISE
        db.commit()
    
    # Background task to send contract to signing service
    background_tasks.add_task(
        enqueue_enterprise_job,
        "contract_signing",
        contract_id=str(db_contract.id),
        company_id=str(company_id)
    )
    
    return {
        "message": "Contract created successfully",
        "contract_id": db_contract.id,
        "contract_number": contract_number,
        "status": db_contract.status.value
    }


@router.post("/contracts/{contract_id}/activate", response_model=dict)
async def activate_contract(
    contract_id: uuid.UUID,
    payment_method: PaymentMethod = PaymentMethod.INVOICE,
    stripe_payment_method_id: Optional[str] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Activate a contract"""
    contract = db.get(EnterpriseContract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    if contract.status != ContractStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract cannot be activated from {contract.status.value} status"
        )
    
    # Update contract status
    contract.status = ContractStatus.ACTIVE
    contract.activated_at = datetime.utcnow()
    contract.payment_method = payment_method
    
    # If using Stripe, create subscription
    if payment_method == PaymentMethod.STRIPE and stripe_payment_method_id:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Create or retrieve Stripe customer
            company = contract.company
            customer = stripe.Customer.create(
                email=company.billing_email or company.support_email,
                name=company.legal_name,
                metadata={
                    "company_id": str(company.id),
                    "contract_id": str(contract.id)
                }
            )
            
            # Create Stripe subscription
            price = stripe.Price.create(
                unit_amount=int(contract.monthly_rate_eur * 100),
                currency="eur",
                recurring={"interval": "month"},
                product_data={"name": f"{contract.plan.value} Plan"},
                metadata={"contract_id": str(contract.id)}
            )
            
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": price.id}],
                default_payment_method=stripe_payment_method_id,
                metadata={"contract_id": str(contract.id)}
            )
            
            contract.stripe_customer_id = customer.id
            contract.stripe_subscription_id = subscription.id
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Payment setup failed: {str(e)}"
            )
    
    db.commit()
    
    # Update company status
    company = contract.company
    company.is_active = True
    company.is_verified = True
    db.commit()
    
    return {
        "message": "Contract activated successfully",
        "contract_id": contract.id,
        "status": contract.status.value
    }


# ==================== ORDER ENDPOINTS ====================
@router.post("/companies/{company_id}/orders", response_model=dict)
async def create_order(
    company_id: uuid.UUID,
    order: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Create simulation order for enterprise"""
    company = db.get(EnterpriseCompany, company_id)
    if not company or not company.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found or inactive"
        )
    
    # Check active contract
    active_contract = db.query(EnterpriseContract).filter(
        EnterpriseContract.company_id == company_id,
        EnterpriseContract.status == ContractStatus.ACTIVE
    ).first()
    
    if not active_contract:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No active contract found"
        )
    
    # Generate order number
    order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    # Create order
    db_order = EnterpriseOrder(
        company_id=company_id,
        contract_id=active_contract.id,
        order_number=order_number,
        status="pending",
        **order.dict(exclude_none=True)
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Create initial job
    db_job = EnterpriseJob(
        order_id=db_order.id,
        job_type=order.simulation_type,
        status="queued",
        priority=order.priority,
        parameters=order.parameters,
        estimated_duration=timedelta(minutes=order.iterations // 1000)
    )
    
    db.add(db_job)
    db.commit()
    
    # Add to job queue
    background_tasks.add_task(
        enqueue_enterprise_job,
        "simulation",
        job_id=str(db_job.id),
        order_id=str(db_order.id),
        parameters=order.parameters
    )
    
    return {
        "message": "Order created successfully",
        "order_id": db_order.id,
        "order_number": order_number,
        "job_id": db_job.id
    }


@router.get("/orders/{order_id}/status", response_model=dict)
async def get_order_status(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get order status and job progress"""
    order = db.get(EnterpriseOrder, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    jobs = db.query(EnterpriseJob).filter(
        EnterpriseJob.order_id == order_id
    ).order_by(desc(EnterpriseJob.created_at)).all()
    
    current_job = jobs[0] if jobs else None
    
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "amount_eur": float(order.amount_eur),
        "created_at": order.created_at,
        "current_job": {
            "id": current_job.id if current_job else None,
            "status": current_job.status if current_job else None,
            "progress": current_job.progress if current_job else None,
            "estimated_completion": current_job.estimated_completion if current_job else None
        } if current_job else None,
        "jobs": [
            {
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status,
                "progress": job.progress,
                "created_at": job.created_at,
                "completed_at": job.completed_at
            }
            for job in jobs[:10]  # Limit to last 10 jobs
        ]
    }


# ==================== INVOICE ENDPOINTS ====================
@router.post("/companies/{company_id}/invoices", response_model=dict)
async def create_invoice(
    company_id: uuid.UUID,
    invoice: InvoiceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Create invoice for company"""
    company = db.get(EnterpriseCompany, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Calculate tax and total
    tax_amount = invoice.subtotal_eur * (invoice.tax_rate / 100)
    total_amount = invoice.subtotal_eur + tax_amount
    
    # Generate invoice number
    invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m')}-{str(uuid.uuid4())[:6].upper()}"
    
    # Create invoice
    db_invoice = EnterpriseInvoice(
        company_id=company_id,
        invoice_number=invoice_number,
        subtotal_eur=invoice.subtotal_eur,
        tax_rate=invoice.tax_rate,
        tax_amount_eur=tax_amount,
        total_eur=total_amount,
        **invoice.dict(exclude_none=True)
    )
    
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    # Background task to send invoice email
    background_tasks.add_task(
        enqueue_enterprise_job,
        "invoice_notification",
        invoice_id=str(db_invoice.id),
        company_id=str(company_id)
    )
    
    return {
        "message": "Invoice created successfully",
        "invoice_id": db_invoice.id,
        "invoice_number": invoice_number,
        "total_eur": float(total_amount),
        "due_date": invoice.due_date
    }


@router.get("/companies/{company_id}/invoices", response_model=List[dict])
async def list_invoices(
    company_id: uuid.UUID,
    status: Optional[str] = Query(None, regex="^(draft|sent|paid|overdue|cancelled)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """List company invoices with filters"""
    company = db.get(EnterpriseCompany, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    query = db.query(EnterpriseInvoice).filter(
        EnterpriseInvoice.company_id == company_id
    )
    
    if status:
        query = query.filter(EnterpriseInvoice.status == status)
    if start_date:
        query = query.filter(EnterpriseInvoice.invoice_date >= start_date)
    if end_date:
        query = query.filter(EnterpriseInvoice.invoice_date <= end_date)
    
    invoices = query.order_by(desc(EnterpriseInvoice.invoice_date)).offset(skip).limit(limit).all()
    
    return [
        {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "due_date": invoice.due_date,
            "subtotal_eur": float(invoice.subtotal_eur),
            "tax_amount_eur": float(invoice.tax_amount_eur),
            "total_eur": float(invoice.total_eur),
            "status": invoice.status,
            "paid_at": invoice.paid_at,
            "created_at": invoice.created_at
        }
        for invoice in invoices
    ]


# ==================== ANALYTICS ENDPOINTS ====================
@router.get("/analytics/companies", response_model=dict)
async def get_companies_analytics(
    timeframe: str = Query("month", regex="^(day|week|month|quarter|year)$"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get companies analytics"""
    now = datetime.utcnow()
    
    if timeframe == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif timeframe == "week":
        start_date = now - timedelta(days=now.weekday())
    elif timeframe == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif timeframe == "quarter":
        month = ((now.month - 1) // 3) * 3 + 1
        start_date = now.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # year
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Total companies
    total_companies = db.query(EnterpriseCompany).count()
    active_companies = db.query(EnterpriseCompany).filter(
        EnterpriseCompany.is_active == True
    ).count()
    
    # New companies in timeframe
    new_companies = db.query(EnterpriseCompany).filter(
        EnterpriseCompany.created_at >= start_date
    ).count()
    
    # Companies by tier
    tier_counts = db.query(
        EnterpriseCompany.tier,
        sa.func.count(EnterpriseCompany.id)
    ).group_by(EnterpriseCompany.tier).all()
    
    # Companies by industry
    industry_counts = db.query(
        EnterpriseCompany.industry,
        sa.func.count(EnterpriseCompany.id)
    ).group_by(EnterpriseCompany.industry).all()
    
    return {
        "timeframe": timeframe,
        "start_date": start_date,
        "end_date": now,
        "total_companies": total_companies,
        "active_companies": active_companies,
        "new_companies": new_companies,
        "companies_by_tier": {
            tier.value if isinstance(tier, CompanyTier) else tier: count
            for tier, count in tier_counts
        },
        "companies_by_industry": {
            industry.value if isinstance(industry, IndustryType) else industry: count
            for industry, count in industry_counts
        }
    }


# ==================== EXPORT ENDPOINTS ====================
@router.post("/exports/companies", response_model=dict)
async def export_companies(
    background_tasks: BackgroundTasks,
    format: str = Query("csv", regex="^(csv|json|xlsx)$"),
    filters: Optional[Dict[str, Any]] = Query(None),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Export companies data"""
    # This would:
    # 1. Generate export job
    # 2. Add to background tasks
    # 3. Return job ID for polling
    
    job_id = str(uuid.uuid4())
    
    background_tasks.add_task(
        enqueue_enterprise_job,
        "export_companies",
        job_id=job_id,
        export_format=format,
        filters=filters or {}
    )
    
    return {
        "message": "Export job created",
        "job_id": job_id,
        "format": format,
        "status": "processing",
        "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    }


# ==================== BULK OPERATIONS ====================
@router.post("/bulk/companies", response_model=dict)
async def bulk_create_companies(
    companies: List[CompanyCreate],
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks
):
    """Bulk create companies"""
    created = 0
    errors = []
    
    for i, company_data in enumerate(companies):
        try:
            # Check for existing company
            existing = db.query(EnterpriseCompany).filter(
                or_(
                    EnterpriseCompany.legal_name == company_data.legal_name,
                    EnterpriseCompany.company_number == company_data.company_number
                )
            ).first()
            
            if existing:
                errors.append({
                    "index": i,
                    "legal_name": company_data.legal_name,
                    "error": "Company already exists"
                })
                continue
            
            # Create company
            db_company = EnterpriseCompany(**company_data.dict(exclude_none=True))
            db.add(db_company)
            created += 1
            
        except Exception as e:
            errors.append({
                "index": i,
                "legal_name": company_data.legal_name,
                "error": str(e)
            })
    
    db.commit()
    
    # Schedule background tasks for each new company
    if created > 0:
        background_tasks.add_task(
            enqueue_enterprise_job,
            "bulk_company_processing",
            count=created
        )
    
    return {
        "message": "Bulk operation completed",
        "created": created,
        "errors": errors,
        "total": len(companies)
    }
