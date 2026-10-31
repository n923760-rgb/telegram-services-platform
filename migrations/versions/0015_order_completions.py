"""Generic atomic completion handoff; no service or hosting entitlement."""

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "order_completions",
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id"), primary_key=True),
        sa.Column("owner_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False, server_default="pending"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("state IN ('pending','applied','discarded')", name="completion_state"),
        sa.CheckConstraint(
            "(state = 'pending') = (payload IS NOT NULL)", name="completion_content"
        ),
        sa.CheckConstraint("expires_at > created_at", name="completion_expiry"),
    )
    op.create_index("ix_order_completions_owner_id", "order_completions", ["owner_id"])
    op.create_index("ix_order_completions_expires_at", "order_completions", ["expires_at"])
    op.create_index(
        "ix_order_completions_pending",
        "order_completions",
        ["expires_at", "order_id"],
        postgresql_where=sa.text("state = 'pending'"),
    )
    op.execute("""CREATE FUNCTION protect_order_completion() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      IF NEW.order_id IS DISTINCT FROM OLD.order_id
        OR NEW.owner_id IS DISTINCT FROM OLD.owner_id
        OR NEW.kind IS DISTINCT FROM OLD.kind
        OR NEW.content_hash IS DISTINCT FROM OLD.content_hash
        OR NEW.created_at IS DISTINCT FROM OLD.created_at
        OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
        OR OLD.state <> 'pending' OR NEW.state NOT IN ('applied','discarded')
        OR NEW.payload IS NOT NULL
      THEN RAISE EXCEPTION 'completion identity/content immutable; only scrub once'; END IF;
      RETURN NEW; END $$""")
    op.execute(
        "CREATE TRIGGER protect_order_completion BEFORE UPDATE ON order_completions FOR EACH ROW EXECUTE FUNCTION protect_order_completion()"
    )


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM order_completions)
      THEN RAISE EXCEPTION 'completion data exists; use a forward fix'; END IF;
      END $$""")
    op.execute("DROP FUNCTION protect_order_completion() CASCADE")
    op.drop_table("order_completions")
