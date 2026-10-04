"""Separate bounded retries from successful confirmation stages."""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "jobs", sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0")
    )


def downgrade():
    op.drop_column("jobs", "failure_count")
