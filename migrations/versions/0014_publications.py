"""Generic durable publications and revision-bound consent; no public routes."""

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "publications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id"), nullable=False, unique=True),
        sa.Column("state", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("latest_revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_revision", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "state IN ('draft','published','suspended','expired','deleted')",
            name="publication_state",
        ),
        sa.CheckConstraint("latest_revision >= 0", name="publication_latest"),
        sa.CheckConstraint(
            "active_revision > 0 AND active_revision <= latest_revision", name="publication_active"
        ),
        sa.CheckConstraint(
            "(state = 'published') = (active_revision IS NOT NULL)", name="publication_visibility"
        ),
    )
    op.create_index("ix_publications_owner_id", "publications", ["owner_id"])
    op.create_index("ix_publications_expires_at", "publications", ["expires_at"])
    op.create_table(
        "publication_revisions",
        sa.Column("publication_id", sa.Uuid(), sa.ForeignKey("publications.id"), primary_key=True),
        sa.Column("number", sa.Integer(), primary_key=True),
        sa.Column("operation_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("base_revision", sa.Integer(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "number > 0 AND base_revision = number - 1", name="publication_revision_sequence"
        ),
    )
    op.create_foreign_key(
        "publication_active_revision_fk",
        "publications",
        "publication_revisions",
        ["id", "active_revision"],
        ["publication_id", "number"],
    )
    op.create_table(
        "publication_consents",
        sa.Column("operation_id", sa.Uuid(), primary_key=True),
        sa.Column("publication_id", sa.Uuid(), sa.ForeignKey("publications.id"), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("previous_active", sa.Integer(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("terms_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("revision > 0", name="publication_consent_revision"),
    )
    op.create_index(
        "ix_publication_consents_publication_id", "publication_consents", ["publication_id"]
    )
    op.execute("""CREATE FUNCTION protect_publication_revision() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      RAISE EXCEPTION 'publication revisions cannot be edited; create a new revision'; END $$""")
    op.execute(
        "CREATE TRIGGER protect_publication_revision BEFORE UPDATE ON publication_revisions FOR EACH ROW EXECUTE FUNCTION protect_publication_revision()"
    )
    op.execute("""CREATE FUNCTION protect_publication_consent() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      RAISE EXCEPTION 'publication consent is immutable'; END $$""")
    op.execute(
        "CREATE TRIGGER protect_publication_consent BEFORE UPDATE OR DELETE ON publication_consents FOR EACH ROW EXECUTE FUNCTION protect_publication_consent()"
    )


def downgrade():
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM publications) OR EXISTS (SELECT 1 FROM publication_consents)
      THEN RAISE EXCEPTION 'publication data exists; retain migration and use a forward fix'; END IF;
      END $$""")
    op.execute("DROP FUNCTION protect_publication_consent() CASCADE")
    op.execute("DROP FUNCTION protect_publication_revision() CASCADE")
    op.drop_table("publication_consents")
    op.drop_constraint("publication_active_revision_fk", "publications", type_="foreignkey")
    op.drop_table("publication_revisions")
    op.drop_table("publications")
