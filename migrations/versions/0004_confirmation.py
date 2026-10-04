"""Generic confirmation support without service-specific core code."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "orders",
        sa.Column(
            "input_schema_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
        ),
    )
    op.execute(
        "UPDATE orders SET input_schema_snapshot = services.input_schema FROM services WHERE orders.service_slug = services.slug"
    )
    op.alter_column("orders", "input_schema_snapshot", server_default=None)
    op.add_column(
        "orders",
        sa.Column(
            "confirmation_notified", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )


def downgrade():
    op.drop_column("orders", "input_schema_snapshot")
    op.drop_column("orders", "confirmation_notified")
