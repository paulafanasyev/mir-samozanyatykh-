"""Security token storage cleanup."""
from alembic import op
import sqlalchemy as sa
revision="v842_security_cleanup"
down_revision="render_v84"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    cols={c["name"] for c in sa.inspect(bind).get_columns("users")}
    # Legacy plaintext tokens are intentionally invalidated rather than copied into the new hash fields.
    # This prevents old password-reset/email-verification tokens from surviving the security migration.
    if "email_verification_token" in cols:
        op.drop_column("users","email_verification_token")
    additions=[
      ("password_reset_token_hash", sa.String(255)),
      ("password_reset_expires_at", sa.DateTime(timezone=True)),
      ("password_reset_created_at", sa.DateTime(timezone=True)),
      ("email_verification_token_hash", sa.String(255)),
      ("email_verification_expires_at", sa.DateTime(timezone=True)),
    ]
    for name,col in additions:
        if name not in cols: op.add_column("users", sa.Column(name, col, nullable=True))

def downgrade():
    raise RuntimeError("Security cleanup downgrade is intentionally disabled: it would reintroduce the legacy plaintext verification-token schema. Restore a pre-migration backup instead.")
