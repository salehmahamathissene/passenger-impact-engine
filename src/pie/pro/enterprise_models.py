from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from sqlalchemy import (
    String, DateTime, Integer, Boolean, Enum, ForeignKey, Numeric, Text, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


# ========================= Enums =========================
class CompanyTier(str, enum.Enum):
    small = "small"
    mid = "mid"
    large = "large"


class IndustryType(str, enum.Enum):
    airline = "airline"
    airport = "airport"
    ground_handler = "ground_handler"
    other = "other"


class SubscriptionPlan(str, enum.Enum):
    basic = "basic"
    pro = "pro"
    enterprise = "enterprise"


class BillingCycle(str, enum.Enum):
    monthly = "monthly"
    yearly = "yearly"


class PaymentMethod(str, enum.Enum):
    invoice = "invoice"
    card = "card"
    bank_transfer = "bank_transfer"


class ContractStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    suspended = "suspended"
    terminated = "terminated"
    expired = "expired"


class EnterpriseOrderStatus(str, enum.Enum):
    created = "created"
    approved = "approved"
    running = "running"
    done = "done"
    failed = "failed"


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    overdue = "overdue"
    void = "void"

class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


# ========================= Models =========================
class EnterpriseCompany(Base):
    __tablename__ = "enterprise_companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    legal_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    trading_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    company_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    vat_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)

    tier: Mapped[CompanyTier] = mapped_column(Enum(CompanyTier), default=CompanyTier.small, nullable=False)
    industry: Mapped[IndustryType] = mapped_column(Enum(IndustryType), default=IndustryType.airline, nullable=False)

    website: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    support_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    billing_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)

    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    annual_revenue_eur: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    total_spent: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    api_key_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    contacts: Mapped[list["EnterpriseContact"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    contracts: Mapped[list["EnterpriseContract"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    orders: Mapped[list["EnterpriseOrder"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    invoices: Mapped[list["EnterpriseInvoice"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class EnterpriseContact(Base):
    __tablename__ = "enterprise_contacts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("enterprise_companies.id"), nullable=False)
    company: Mapped["EnterpriseCompany"] = relationship(back_populates="contacts")

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)

    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    job_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_technical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_billing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    can_receive_emails: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_receive_sms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EnterpriseContract(Base):
    __tablename__ = "enterprise_contracts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("enterprise_companies.id"), nullable=False)
    company: Mapped["EnterpriseCompany"] = relationship(back_populates="contracts")

    contract_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)

    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), default=ContractStatus.draft, nullable=False)
    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan), nullable=False)
    billing_cycle: Mapped[BillingCycle] = mapped_column(Enum(BillingCycle), default=BillingCycle.monthly, nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), default=PaymentMethod.invoice, nullable=False)

    monthly_rate_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    setup_fee_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)

    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    renewal_notice_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    max_monthly_simulations: Mapped[int] = mapped_column(Integer, nullable=False)
    max_concurrent_jobs: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    priority_support: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dedicated_account_manager: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    sla_response_time_hours: Mapped[int] = mapped_column(Integer, default=48, nullable=False)
    sla_uptime_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("99.5"), nullable=False)


class EnterpriseOrder(Base):
    __tablename__ = "enterprise_orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("enterprise_companies.id"), nullable=False)
    company: Mapped["EnterpriseCompany"] = relationship(back_populates="orders")

    contract_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("enterprise_contracts.id"), nullable=True)
    contract: Mapped[Optional["EnterpriseContract"]] = relationship()

    description: Mapped[str] = mapped_column(String(500), nullable=False)
    simulation_type: Mapped[str] = mapped_column(String(100), nullable=False)

    iterations: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    amount_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    status: Mapped[EnterpriseOrderStatus] = mapped_column(Enum(EnterpriseOrderStatus), default=EnterpriseOrderStatus.created, nullable=False)

    job: Mapped[Optional["EnterpriseJob"]] = relationship(back_populates="order", uselist=False, cascade="all, delete-orphan")


class EnterpriseJob(Base):
    __tablename__ = "enterprise_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("enterprise_orders.id"), nullable=False, unique=True)
    order: Mapped["EnterpriseOrder"] = relationship(back_populates="job")

    status: Mapped[EnterpriseOrderStatus] = mapped_column(Enum(EnterpriseOrderStatus), default=EnterpriseOrderStatus.created, nullable=False)
    artifact_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    runs_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class EnterpriseInvoice(Base):
    __tablename__ = "enterprise_invoices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("enterprise_companies.id"), nullable=False)
    company: Mapped["EnterpriseCompany"] = relationship(back_populates="invoices")

    invoice_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.draft, nullable=False)

    invoice_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    subtotal_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    tax_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    total_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    line_items: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
