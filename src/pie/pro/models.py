from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    sponsored = "sponsored"
    failed = "failed"


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Customer info
    customer_email: Mapped[str] = mapped_column(String(320), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), nullable=False)  # starter, pro, enterprise
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="eur", nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)
    
    # Stripe
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stripe_checkout_session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationship
    job: Mapped[Optional["Job"]] = relationship(back_populates="order", uselist=False, cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.queued, nullable=False)
    
    # Artifact
    artifact_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Performance metrics
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    runs_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationship
    order: Mapped["Order"] = relationship(back_populates="job")
