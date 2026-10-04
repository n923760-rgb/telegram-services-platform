"""Freeze plugin versions for customer orders."""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "services", sa.Column("version", sa.String(32), nullable=False, server_default="1")
    )
    op.add_column(
        "orders", sa.Column("service_version", sa.String(32), nullable=False, server_default="1")
    )


def downgrade():
    op.drop_column("orders", "service_version")
    op.drop_column("services", "version")
