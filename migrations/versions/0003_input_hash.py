"""Preserve idempotency without retaining user content after expiry."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("orders", sa.Column("input_hash", sa.String(64), nullable=True))
    # Existing orders were created before fingerprint support. Mark them as legacy,
    # retaining their input comparison path in application code during this migration.
    op.execute("UPDATE orders SET input_hash = 'legacy' WHERE input_hash IS NULL")
    op.alter_column("orders", "input_hash", nullable=False)


def downgrade():
    op.drop_column("orders", "input_hash")
