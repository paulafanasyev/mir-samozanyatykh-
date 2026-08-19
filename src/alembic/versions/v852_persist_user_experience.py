"""Persist white-label, Svetlana history and email campaigns."""
from alembic import op
import sqlalchemy as sa

revision = "v852_persist_user_experience"
down_revision = "v851_fns_document_integrity"
branch_labels = None
depends_on = None


def _tables(bind):
    return {t for t in sa.inspect(bind).get_table_names()}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "branding_settings" not in columns:
        op.add_column("users", sa.Column("branding_settings", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
        op.alter_column("users", "branding_settings", server_default=None)

    tables = _tables(bind)
    if "svetlana_chat_messages" not in tables:
        op.create_table(
            "svetlana_chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("role", sa.String(20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_svetlana_chat_messages_user_id", "svetlana_chat_messages", ["user_id"])
        op.create_index("ix_svetlana_chat_messages_created_at", "svetlana_chat_messages", ["created_at"])

    if "email_campaigns" not in tables:
        op.create_table(
            "email_campaigns",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("subject", sa.String(255), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
            sa.Column("recipient_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("opened_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_email_campaigns_user_id", "email_campaigns", ["user_id"])
        op.create_index("ix_email_campaigns_created_at", "email_campaigns", ["created_at"])


def downgrade():
    bind = op.get_bind()
    tables = _tables(bind)
    if "email_campaigns" in tables:
        op.drop_index("ix_email_campaigns_created_at", table_name="email_campaigns")
        op.drop_index("ix_email_campaigns_user_id", table_name="email_campaigns")
        op.drop_table("email_campaigns")
    if "svetlana_chat_messages" in tables:
        op.drop_index("ix_svetlana_chat_messages_created_at", table_name="svetlana_chat_messages")
        op.drop_index("ix_svetlana_chat_messages_user_id", table_name="svetlana_chat_messages")
        op.drop_table("svetlana_chat_messages")
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "branding_settings" in columns:
        op.drop_column("users", "branding_settings")
