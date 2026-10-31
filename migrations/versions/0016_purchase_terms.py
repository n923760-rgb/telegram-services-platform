"""Immutable generic reviewed purchase terms, separate from Stars payment terms."""

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("orders", sa.Column("purchase_terms_hash", sa.String(64), nullable=True))
    op.add_column(
        "orders", sa.Column("purchase_terms_snapshot", sa.JSON(none_as_null=True), nullable=True)
    )
    op.create_check_constraint(
        "order_purchase_terms_pair",
        "orders",
        "(purchase_terms_hash IS NULL) = (purchase_terms_snapshot IS NULL)",
    )
    op.execute("""CREATE FUNCTION protect_order_purchase_terms() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      IF NEW.purchase_terms_hash IS DISTINCT FROM OLD.purchase_terms_hash
         OR NEW.purchase_terms_snapshot::text IS DISTINCT FROM OLD.purchase_terms_snapshot::text
      THEN RAISE EXCEPTION 'reviewed purchase terms are immutable'; END IF;
      RETURN NEW; END $$""")
    op.execute(
        "CREATE TRIGGER protect_order_purchase_terms BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION protect_order_purchase_terms()"
    )


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM orders WHERE purchase_terms_hash IS NOT NULL)
      THEN RAISE EXCEPTION 'purchase evidence exists; use a forward fix'; END IF;
      END $$""")
    op.execute("DROP FUNCTION protect_order_purchase_terms() CASCADE")
    op.drop_constraint("order_purchase_terms_pair", "orders", type_="check")
    op.drop_column("orders", "purchase_terms_snapshot")
    op.drop_column("orders", "purchase_terms_hash")
