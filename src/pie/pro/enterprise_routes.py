"""
Enterprise routes for Passenger Impact Engine
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from .db import get_db
from .settings import get_settings
from .enterprise_models import EnterpriseCompany, EnterpriseContact, EnterpriseContract, EnterpriseInvoice

router = APIRouter()
settings = get_settings()

def verify_admin_key(x_admin_key: str = Header(None)):
    """Verify admin key for enterprise endpoints"""
    if not x_admin_key:
        raise HTTPException(status_code=401, detail="Admin key required")
    if x_admin_key != settings.ENTERPRISE_ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return x_admin_key

@router.get("/health")
async def health(db: Session = Depends(get_db), admin_key: str = Depends(verify_admin_key)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "service": "enterprise",
            "admin_key_valid": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/companies")
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_key: str = Depends(verify_admin_key)
):
    """List all companies"""
    companies = db.query(EnterpriseCompany).offset(skip).limit(limit).all()
    return {
        "companies": companies,
        "total": len(companies),
        "skip": skip,
        "limit": limit
    }

@router.post("/companies")
async def create_company(
    company_data: dict,
    db: Session = Depends(get_db),
    admin_key: str = Depends(verify_admin_key)
):
    """Create a new company"""
    try:
        company = EnterpriseCompany(
            legal_name=company_data.get("legal_name"),
            trading_name=company_data.get("trading_name"),
            tier=company_data.get("tier", "small"),
            industry=company_data.get("industry"),
            country=company_data.get("country", "US"),
            contact_email=company_data.get("contact_email"),
            contact_phone=company_data.get("contact_phone")
        )
        
        db.add(company)
        db.commit()
        db.refresh(company)
        
        return {
            "message": "Company created successfully",
            "id": company.id,
            "company": {
                "legal_name": company.legal_name,
                "trading_name": company.trading_name,
                "tier": company.tier
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

@router.get("/companies/{company_id}")
async def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    admin_key: str = Depends(verify_admin_key)
):
    """Get company by ID"""
    company = db.query(EnterpriseCompany).filter(EnterpriseCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.post("/companies/{company_id}/contacts")
async def create_contact(
    company_id: str,
    contact_data: dict,
    db: Session = Depends(get_db),
    admin_key: str = Depends(verify_admin_key)
):
    """Create a contact for a company"""
    # Check if company exists
    company = db.query(EnterpriseCompany).filter(EnterpriseCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        contact = EnterpriseContact(
            company_id=company_id,
            first_name=contact_data.get("first_name"),
            last_name=contact_data.get("last_name"),
            email=contact_data.get("email"),
            phone=contact_data.get("phone"),
            role=contact_data.get("role", "operations_manager"),
            department=contact_data.get("department", "operations")
        )
        
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        return {
            "message": "Contact created successfully",
            "id": contact.id,
            "contact": {
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email": contact.email
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create contact: {str(e)}")

@router.get("/contracts")
async def list_contracts(
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_key: str = Depends(verify_admin_key)
):
    """List contracts"""
    query = db.query(EnterpriseContract)
    if company_id:
        query = query.filter(EnterpriseContract.company_id == company_id)
    
    contracts = query.offset(skip).limit(limit).all()
    return {
        "contracts": contracts,
        "total": len(contracts),
        "skip": skip,
        "limit": limit
    }

@router.get("/invoices")
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_key: str = Depends(verify_admin_key)
):
    """List invoices"""
    query = db.query(EnterpriseInvoice)
    if company_id:
        query = query.filter(EnterpriseInvoice.company_id == company_id)
    
    invoices = query.offset(skip).limit(limit).all()
    return {
        "invoices": invoices,
        "total": len(invoices),
        "skip": skip,
        "limit": limit
    }

@router.get("/search")
async def search_enterprise(
    q: str = "",
    db: Session = Depends(get_db),
    admin_key: str = Depends(verify_admin_key)
):
    """Search across enterprise entities"""
    if not q:
        return {"results": []}
    
    # Search companies
    companies = db.query(EnterpriseCompany).filter(
        (EnterpriseCompany.legal_name.ilike(f"%{q}%")) |
        (EnterpriseCompany.trading_name.ilike(f"%{q}%"))
    ).limit(10).all()
    
    # Search contacts
    contacts = db.query(EnterpriseContact).filter(
        (EnterpriseContact.first_name.ilike(f"%{q}%")) |
        (EnterpriseContact.last_name.ilike(f"%{q}%")) |
        (EnterpriseContact.email.ilike(f"%{q}%"))
    ).limit(10).all()
    
    return {
        "query": q,
        "companies": companies,
        "contacts": contacts,
        "total_results": len(companies) + len(contacts)
    }