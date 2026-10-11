"""Immutable owner-set Stars selling price changes."""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "star_price_changes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.BigInteger(), nullable=False),
        sa.Column("service_slug", sa.String(64), sa.ForeignKey("services.slug"), nullable=False),
        sa.Column("old_price", sa.Integer(), nullable=True),
        sa.Column("new_price", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "old_price IS NULL OR old_price BETWEEN 1 AND 1000000", name="price_change_old"
        ),
        sa.CheckConstraint("new_price BETWEEN 1 AND 1000000", name="price_change_new"),
    )
    op.create_index("ix_star_price_changes_service_slug", "star_price_changes", ["service_slug"])
    op.execute("""CREATE FUNCTION protect_star_price_change() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      RAISE EXCEPTION 'price change audit is immutable'; END $$""")
    op.execute(
        "CREATE TRIGGER protect_star_price_change BEFORE UPDATE OR DELETE ON star_price_changes FOR EACH ROW EXECUTE FUNCTION protect_star_price_change()"
    )


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM star_price_changes)
      THEN RAISE EXCEPTION 'price audit exists; retain migration and use a forward fix'; END IF;
      END $$""")
    op.execute("DROP FUNCTION protect_star_price_change() CASCADE")
    op.drop_table("star_price_changes")
