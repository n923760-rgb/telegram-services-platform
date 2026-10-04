"""Enforce signed ledger operation arithmetic in PostgreSQL."""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None
CONSTRAINT = """(kind IN ('credit','refund') AND available_delta > 0 AND reserved_delta = 0)
 OR (kind='reserve' AND available_delta < 0 AND reserved_delta = -available_delta)
 OR (kind='capture' AND available_delta = 0 AND reserved_delta < 0)
 OR (kind='release' AND available_delta > 0 AND reserved_delta = -available_delta)"""


def upgrade():
    op.create_check_constraint("ledger_operation_signs", "wallet_ledger", CONSTRAINT)


def downgrade():
    op.drop_constraint("ledger_operation_signs", "wallet_ledger", type_="check")
