"""Audit returned-usage pricing and distinguish cancelled jobs."""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("jobs", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_jobs_finished_at", "jobs", ["finished_at"])
    op.execute(
        "UPDATE jobs SET finished_at=orders.updated_at FROM orders WHERE jobs.order_id=orders.id AND jobs.status IN ('done','failed')"
    )
    op.add_column(
        "cost_usage", sa.Column("provider", sa.String(80), nullable=False, server_default="unknown")
    )
    op.add_column(
        "cost_usage", sa.Column("model", sa.String(120), nullable=False, server_default="unknown")
    )
    op.add_column(
        "cost_usage", sa.Column("rate_snapshot", sa.JSON(), nullable=False, server_default="{}")
    )
    op.execute(
        "UPDATE jobs SET status='cancelled' FROM orders WHERE jobs.order_id=orders.id AND orders.status='cancelled' AND jobs.status='failed'"
    )


def downgrade():
    op.drop_index("ix_jobs_finished_at", table_name="jobs")
    op.drop_column("jobs", "finished_at")
    op.execute("UPDATE jobs SET status='failed' WHERE status='cancelled'")
    op.drop_column("cost_usage", "rate_snapshot")
    op.drop_column("cost_usage", "model")
    op.drop_column("cost_usage", "provider")
