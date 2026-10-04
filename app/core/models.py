from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    language: Mapped[str] = mapped_column(String(2), default="ar")
    banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Service(Base):
    __tablename__ = "services"
    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(32), default="1", server_default="1")
    name_ar: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str] = mapped_column(String(200))
    description_ar: Mapped[str] = mapped_column(String(1000))
    price_halala: Mapped[int] = mapped_column(BigInteger)
    input_schema: Mapped[dict] = mapped_column(JSON)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (CheckConstraint("price_halala > 0"),)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    service_slug: Mapped[str] = mapped_column(ForeignKey("services.slug"), index=True)
    price_halala: Mapped[int] = mapped_column(BigInteger)
    idempotency_key: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    service_version: Mapped[str] = mapped_column(String(32), default="1", server_default="1")
    input_schema_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    input_hash: Mapped[str] = mapped_column(String(64))
    inputs: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    files_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", index=True
    )
    confirmation_notified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    failure_notified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    error_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key"),
        CheckConstraint("price_halala > 0"),
    )


class Ledger(Base):
    __tablename__ = "wallet_ledger"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("orders.id"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(20))
    available_delta: Mapped[int] = mapped_column(BigInteger)
    reserved_delta: Mapped[int] = mapped_column(BigInteger)
    idempotency_key: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key"),
        UniqueConstraint("idempotency_key", name="uq_wallet_ledger_idempotency_key"),
        UniqueConstraint("order_id", "kind"),
        CheckConstraint("kind IN ('credit','reserve','capture','release','refund')"),
        CheckConstraint(
            "(kind IN ('credit','refund') AND available_delta > 0 AND reserved_delta = 0) OR (kind='reserve' AND available_delta < 0 AND reserved_delta = -available_delta) OR (kind='capture' AND available_delta = 0 AND reserved_delta < 0) OR (kind='release' AND available_delta > 0 AND reserved_delta = -available_delta)",
            name="ledger_operation_signs",
        ),
    )


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    failure_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    cost_sar: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal("0"))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("cost_sar >= 0"),)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)


class CostBudget(Base):
    __tablename__ = "cost_budgets"
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    spent: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal("0"))
    reserved: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal("0"))
    __table_args__ = (CheckConstraint("spent >= 0 AND reserved >= 0"),)


class CostHold(Base):
    __tablename__ = "cost_holds"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id"), index=True)
    global_key: Mapped[str] = mapped_column(String(120))
    user_key: Mapped[str] = mapped_column(String(120))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("amount > 0"),)


class CostUsage(Base):
    __tablename__ = "cost_usage"
    provider: Mapped[str] = mapped_column(String(80), default="unknown", server_default="unknown")
    model: Mapped[str] = mapped_column(String(120), default="unknown", server_default="unknown")
    rate_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    hold_id: Mapped[UUID] = mapped_column(ForeignKey("cost_holds.id"), unique=True)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id"), index=True)
    cost_sar: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("cost_sar >= 0"),)


class JobAttempt(Base):
    __tablename__ = "job_attempts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(ForeignKey("jobs.id"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="running")
    error_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (UniqueConstraint("job_id", "number"),)


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[UUID | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
