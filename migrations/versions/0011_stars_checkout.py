"""Independent Stars prices, direct checkout and immutable receipt/event audit."""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("services", sa.Column("price_stars", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "service_stars_price",
        "services",
        "price_stars IS NULL OR price_stars BETWEEN 1 AND 1000000",
    )
    op.add_column(
        "orders",
        sa.Column("payment_mode", sa.String(16), nullable=False, server_default="test_credit"),
    )
    op.add_column("orders", sa.Column("price_stars", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("terms_version", sa.String(80), nullable=True))
    op.add_column("orders", sa.Column("terms_hash", sa.String(64), nullable=True))
    op.add_column("orders", sa.Column("terms_snapshot", sa.JSON(none_as_null=True), nullable=True))
    op.create_check_constraint(
        "order_payment_contract",
        "orders",
        "(payment_mode='test_credit' AND price_stars IS NULL AND terms_version IS NULL AND terms_hash IS NULL AND terms_snapshot IS NULL) OR (payment_mode='stars' AND price_stars IS NOT NULL AND price_stars BETWEEN 1 AND 1000000 AND terms_version IS NOT NULL AND terms_hash IS NOT NULL AND terms_snapshot IS NOT NULL)",
    )
    op.create_table(
        "star_checkouts",
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id"), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("query_id", sa.String(200), unique=True, nullable=True),
    )
    op.create_table(
        "star_charges",
        sa.Column("charge_id", sa.String(255), primary_key=True),
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("payload", sa.String(128), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("lease_token", sa.Uuid(), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("amount BETWEEN 1 AND 1000000", name="star_charge_amount"),
        sa.CheckConstraint(
            "state IN ('paid','refund_pending','refunding','refund_uncertain','refunded')",
            name="star_charge_state",
        ),
    )
    op.add_column("star_charges", sa.Column("accepted", sa.Boolean(), nullable=False))
    op.create_check_constraint(
        "star_charge_accepted_order", "star_charges", "NOT accepted OR order_id IS NOT NULL"
    )
    op.create_index(
        "uq_star_accepted_order",
        "star_charges",
        ["order_id"],
        unique=True,
        postgresql_where=sa.text("accepted"),
    )
    for field in ("order_id", "user_id", "state"):
        op.create_index(f"ix_star_charges_{field}", "star_charges", [field])
    op.create_table(
        "star_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "charge_id", sa.String(255), sa.ForeignKey("star_charges.charge_id"), nullable=False
        ),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("charge_id", "kind"),
        sa.CheckConstraint(
            "kind IN ('received','refund_requested','refund_started','refund_uncertain','refunded')",
            name="star_event_kind",
        ),
    )
    op.create_index("ix_star_events_charge_id", "star_events", ["charge_id"])
    op.execute("""CREATE FUNCTION protect_star_charge() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'payment receipt is immutable'; END IF;
      IF (NEW.charge_id,NEW.order_id,NEW.user_id,NEW.amount,NEW.accepted,NEW.payload,NEW.created_at)
         IS DISTINCT FROM (OLD.charge_id,OLD.order_id,OLD.user_id,OLD.amount,OLD.accepted,OLD.payload,OLD.created_at)
      THEN RAISE EXCEPTION 'payment receipt is immutable'; END IF;
      IF NEW.state IS DISTINCT FROM OLD.state AND NOT (
        (OLD.state='paid' AND NEW.state IN ('refund_pending','refunded')) OR
        (OLD.state='refund_pending' AND NEW.state IN ('refunding','refunded')) OR
        (OLD.state='refunding' AND NEW.state IN ('refund_uncertain','refunded')) OR
        (OLD.state='refund_uncertain' AND NEW.state='refunded'))
      THEN RAISE EXCEPTION 'invalid payment state transition'; END IF;
      RETURN NEW; END $$""")
    op.execute(
        "CREATE TRIGGER protect_star_charge BEFORE UPDATE OR DELETE ON star_charges FOR EACH ROW EXECUTE FUNCTION protect_star_charge()"
    )
    op.execute("""CREATE FUNCTION protect_star_event() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      RAISE EXCEPTION 'payment events are immutable'; END $$""")
    op.execute(
        "CREATE TRIGGER protect_star_event BEFORE UPDATE OR DELETE ON star_events FOR EACH ROW EXECUTE FUNCTION protect_star_event()"
    )
    op.execute("""CREATE FUNCTION protect_order_payment() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      IF (NEW.payment_mode,NEW.price_stars,NEW.terms_version,NEW.terms_hash,NEW.terms_snapshot::text)
         IS DISTINCT FROM (OLD.payment_mode,OLD.price_stars,OLD.terms_version,OLD.terms_hash,OLD.terms_snapshot::text)
      THEN RAISE EXCEPTION 'order payment contract is immutable'; END IF;
      RETURN NEW; END $$""")
    op.execute(
        "CREATE TRIGGER protect_order_payment BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION protect_order_payment()"
    )


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM star_charges) OR EXISTS (SELECT 1 FROM orders WHERE payment_mode='stars')
      THEN RAISE EXCEPTION 'Stars audit exists; retain migration and use a forward fix'; END IF;
      END $$""")
    op.execute("DROP FUNCTION protect_star_event() CASCADE")
    op.execute("DROP FUNCTION protect_order_payment() CASCADE")
    op.execute("DROP FUNCTION protect_star_charge() CASCADE")
    op.drop_table("star_events")
    op.drop_table("star_charges")
    op.drop_table("star_checkouts")
    op.drop_constraint("order_payment_contract", "orders", type_="check")
    for field in ("terms_snapshot", "terms_hash", "terms_version", "price_stars", "payment_mode"):
        op.drop_column("orders", field)
    op.drop_constraint("service_stars_price", "services", type_="check")
    op.drop_column("services", "price_stars")
