"""Immutable administrator activation decisions and durable cancellation tasks."""

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "service_activation_changes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.BigInteger(), nullable=False),
        sa.Column("service_slug", sa.String(64), sa.ForeignKey("services.slug"), nullable=False),
        sa.Column("old_enabled", sa.Boolean(), nullable=False),
        sa.Column("new_enabled", sa.Boolean(), nullable=False),
        sa.Column("snapshot_hash", sa.String(64), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("old_enabled <> new_enabled", name="activation_state_change"),
        sa.CheckConstraint("actor_id > 0", name="activation_actor"),
    )
    op.create_index(
        "ix_service_activation_changes_service_slug", "service_activation_changes", ["service_slug"]
    )
    op.create_table(
        "service_activation_tasks",
        sa.Column(
            "change_id", sa.Uuid(), sa.ForeignKey("service_activation_changes.id"), primary_key=True
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_service_activation_tasks_completed_at", "service_activation_tasks", ["completed_at"]
    )
    op.execute("""CREATE FUNCTION protect_service_activation_change() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      RAISE EXCEPTION 'activation change audit is immutable'; END $$""")
    op.execute(
        "CREATE TRIGGER protect_service_activation_change BEFORE UPDATE OR DELETE ON service_activation_changes FOR EACH ROW EXECUTE FUNCTION protect_service_activation_change()"
    )


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM service_activation_changes)
      THEN RAISE EXCEPTION 'activation audit exists; retain migration and use a forward fix'; END IF;
      END $$""")
    op.drop_table("service_activation_tasks")
    op.execute("DROP FUNCTION protect_service_activation_change() CASCADE")
    op.drop_table("service_activation_changes")
