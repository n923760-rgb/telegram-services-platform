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
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
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
    price_stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_schema: Mapped[dict] = mapped_column(JSON)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (
        CheckConstraint("price_halala > 0"),
        CheckConstraint(
            "price_stars IS NULL OR price_stars BETWEEN 1 AND 1000000", name="service_stars_price"
        ),
    )


class StarPriceChange(Base):
    __tablename__ = "star_price_changes"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_id: Mapped[int] = mapped_column(BigInteger)
    service_slug: Mapped[str] = mapped_column(ForeignKey("services.slug"), index=True)
    old_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_price: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint(
            "old_price IS NULL OR old_price BETWEEN 1 AND 1000000", name="price_change_old"
        ),
        CheckConstraint("new_price BETWEEN 1 AND 1000000", name="price_change_new"),
    )


class ServiceActivationChange(Base):
    __tablename__ = "service_activation_changes"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_id: Mapped[int] = mapped_column(BigInteger)
    service_slug: Mapped[str] = mapped_column(ForeignKey("services.slug"), index=True)
    old_enabled: Mapped[bool] = mapped_column(Boolean)
    new_enabled: Mapped[bool] = mapped_column(Boolean)
    snapshot_hash: Mapped[str] = mapped_column(String(64))
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("old_enabled <> new_enabled", name="activation_state_change"),
        CheckConstraint("actor_id > 0", name="activation_actor"),
    )


class ServiceActivationTask(Base):
    __tablename__ = "service_activation_tasks"
    change_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_activation_changes.id"), primary_key=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    service_slug: Mapped[str] = mapped_column(ForeignKey("services.slug"), index=True)
    price_halala: Mapped[int] = mapped_column(BigInteger)
    payment_mode: Mapped[str] = mapped_column(
        String(16), default="test_credit", server_default="test_credit"
    )
    price_stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    terms_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    terms_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    terms_snapshot: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
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
        CheckConstraint(
            "(payment_mode='test_credit' AND price_stars IS NULL AND terms_version IS NULL AND terms_hash IS NULL AND terms_snapshot IS NULL) OR (payment_mode='stars' AND price_stars IS NOT NULL AND price_stars BETWEEN 1 AND 1000000 AND terms_version IS NOT NULL AND terms_hash IS NOT NULL AND terms_snapshot IS NOT NULL)",
            name="order_payment_contract",
        ),
    )


class OrderCompletion(Base):
    __tablename__ = "order_completions"
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16), server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    __table_args__ = (
        CheckConstraint("state IN ('pending','applied','discarded')", name="completion_state"),
        CheckConstraint("(state = 'pending') = (payload IS NOT NULL)", name="completion_content"),
        CheckConstraint("expires_at > created_at", name="completion_expiry"),
        Index(
            "ix_order_completions_pending",
            "expires_at",
            "order_id",
            postgresql_where=text("state = 'pending'"),
        ),
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


class StarCheckout(Base):
    __tablename__ = "star_checkouts"
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    query_id: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)


class StarCharge(Base):
    __tablename__ = "star_charges"
    charge_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("orders.id"), index=True, nullable=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    accepted: Mapped[bool] = mapped_column(Boolean)
    payload: Mapped[str] = mapped_column(String(128))
    state: Mapped[str] = mapped_column(String(24), index=True)
    lease_token: Mapped[UUID | None] = mapped_column(nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index("uq_star_accepted_order", "order_id", unique=True, postgresql_where=text("accepted")),
        CheckConstraint("NOT accepted OR order_id IS NOT NULL", name="star_charge_accepted_order"),
        CheckConstraint("amount BETWEEN 1 AND 1000000", name="star_charge_amount"),
        CheckConstraint(
            "state IN ('paid','refund_pending','refunding','refund_uncertain','refunded')",
            name="star_charge_state",
        ),
    )


class StarEvent(Base):
    __tablename__ = "star_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    charge_id: Mapped[str] = mapped_column(ForeignKey("star_charges.charge_id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("charge_id", "kind"),
        CheckConstraint(
            "kind IN ('received','refund_requested','refund_started','refund_uncertain','refunded')",
            name="star_event_kind",
        ),
    )


class Publication(Base):
    """Durable public-content ownership, separate from expiring order artifacts."""

    __tablename__ = "publications"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), unique=True)
    state: Mapped[str] = mapped_column(String(16), default="draft", server_default="draft")
    latest_revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    active_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft','published','suspended','expired','deleted')",
            name="publication_state",
        ),
        CheckConstraint("latest_revision >= 0", name="publication_latest"),
        CheckConstraint(
            "active_revision > 0 AND active_revision <= latest_revision", name="publication_active"
        ),
        CheckConstraint(
            "(state = 'published') = (active_revision IS NOT NULL)", name="publication_visibility"
        ),
        ForeignKeyConstraint(
            ["id", "active_revision"],
            ["publication_revisions.publication_id", "publication_revisions.number"],
            name="publication_active_revision_fk",
            use_alter=True,
        ),
    )


class PublicationRevision(Base):
    __tablename__ = "publication_revisions"
    publication_id: Mapped[UUID] = mapped_column(ForeignKey("publications.id"), primary_key=True)
    number: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[UUID] = mapped_column(unique=True)
    base_revision: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint(
            "number > 0 AND base_revision = number - 1", name="publication_revision_sequence"
        ),
    )


class PublicationConsent(Base):
    """Minimal consent receipt; retains hashes, never a copy of public content."""

    __tablename__ = "publication_consents"
    operation_id: Mapped[UUID] = mapped_column(primary_key=True)
    publication_id: Mapped[UUID] = mapped_column(ForeignKey("publications.id"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    revision: Mapped[int] = mapped_column(Integer)
    previous_active: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    terms_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("revision > 0", name="publication_consent_revision"),)
