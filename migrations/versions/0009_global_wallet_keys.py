"""Bind a ledger operation key globally to its original customer and payload.

Abort rather than rewrite history if a legacy database contains duplicate keys.
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_wallet_ledger_idempotency_key", "wallet_ledger", ["idempotency_key"]
    )


def downgrade():
    op.drop_constraint("uq_wallet_ledger_idempotency_key", "wallet_ledger", type_="unique")
