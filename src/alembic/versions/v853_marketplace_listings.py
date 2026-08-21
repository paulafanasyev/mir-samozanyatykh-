"""Persistent marketplace listings and secure file metadata."""
from alembic import op
import sqlalchemy as sa

revision = "v853_marketplace_listings"
down_revision = "v852_persist_user_experience"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "marketplace_listings" not in tables:
        op.create_table(
            "marketplace_listings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("account_type", sa.String(40), nullable=False),
            sa.Column("kind", sa.String(80), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("direction", sa.String(120), nullable=True),
            sa.Column("contact_email", sa.String(255), nullable=True),
            sa.Column("inn", sa.String(20), nullable=True, index=True),
            sa.Column("verification_status", sa.String(40), nullable=False, server_default="pending"),
            sa.Column("moderation_status", sa.String(40), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_marketplace_listings_status", "marketplace_listings", ["moderation_status", "created_at"])
    if "marketplace_files" not in tables:
        op.create_table(
            "marketplace_files",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("listing_id", sa.Integer(), sa.ForeignKey("marketplace_listings.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("original_name", sa.String(255), nullable=False),
            sa.Column("stored_path", sa.String(500), nullable=False),
            sa.Column("content_type", sa.String(120), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("sha256", sa.String(64), nullable=False, index=True),
            sa.Column("scan_status", sa.String(40), nullable=False, server_default="quarantine"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )


def downgrade():
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "marketplace_files" in tables:
        op.drop_table("marketplace_files")
    if "marketplace_listings" in tables:
        op.drop_index("ix_marketplace_listings_status", table_name="marketplace_listings")
        op.drop_table("marketplace_listings")
