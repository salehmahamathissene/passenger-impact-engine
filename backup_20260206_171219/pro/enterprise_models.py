from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String, DateTime, Boolean, Enum, ForeignKey, Numeric, Text, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class CompanyTier(str, enum.Enum):
    small = "small"
    mid = "mid"
    large = "large"


class IndustryType(str, enum.Enum):
    airline = "airline"
    airport = "airport"
    ground_handler = "ground_handler"
    other = "other"


class ContractStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    terminated = "terminated"


class InvoiceStatus(str, enum.Enum):
    issued = "issued"
    paid = "paid"
    void = "void"
    overdue = "overdue"


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class EnterpriseCompany(Base):
    __tablename__ = "enterprise_companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    trading_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tier: Mapped[CompanyTier] = mapped_column(Enum(CompanyTier), nullable=False, default=CompanyTier.small)
    industry: Mapped[IndustryType] = mapped_column(Enum(IndustryType), nullable=False, default=IndustryType.airline)

    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    support_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Enterprise API key hashing (store ONLY hash)
    api_key_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    contracts: Mapped[list["EnterpriseContract"]] = relationship(back_populates="company")
    invoices: Mapped[list["EnterpriseInvoice"]] = relationship(back_populates="company")
    orders: Mapped[list["EnterpriseOrder"]] = relationship(back_populates="company")


class EnterpriseContract(Base):
    __tablename__ = "enterprise_contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enterprise_companies.id"), nullable=False)

    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), nullable=False, default=ContractStatus.active)
    monthly_allowance_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=100000)
    max_concurrent_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    monthly_fee_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    company: Mapped["EnterpriseCompany"] = relationship(back_populates="contracts")


class EnterpriseInvoice(Base):
    __tablename__ = "enterprise_invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enterprise_companies.id"), nullable=False)

    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.issued)

    subtotal_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    company: Mapped["EnterpriseCompany"] = relationship(back_populates="invoices")


class EnterpriseOrder(Base):
    __tablename__ = "enterprise_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enterprise_companies.id"), nullable=False)
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("enterprise_invoices.id"), nullable=True)

    description: Mapped[str] = mapped_column(String(500), nullable=False)
    iterations: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    company: Mapped["EnterpriseCompany"] = relationship(back_populates="orders")


class EnterpriseJob(Base):
    __tablename__ = "enterprise_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("enterprise_orders.id"), nullable=False, unique=True)

    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), nullable=False, default=JobStatus.queued)
    artifact_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    runs_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
