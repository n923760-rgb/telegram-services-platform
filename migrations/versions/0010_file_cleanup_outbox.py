"""Recover terminal file cleanup, including early cancellations."""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "orders", sa.Column("files_deleted", sa.Boolean(), nullable=False, server_default="false")
    )
    op.create_index("ix_orders_files_deleted", "orders", ["files_deleted"])


def downgrade():
    op.drop_index("ix_orders_files_deleted", table_name="orders")
    op.drop_column("orders", "files_deleted")
