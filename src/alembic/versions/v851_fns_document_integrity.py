"""FNS receipt/document integrity.

Revision ID: v851_fns_document_integrity
Revises: v850_tax_financial_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "v851_fns_document_integrity"
down_revision = "v850_tax_financial_integrity"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "uq_fns_receipts_user_fns_id" not in {c.get("name") for c in sa.inspect(bind).get_unique_constraints("fns_receipts")}:
        op.create_unique_constraint("uq_fns_receipts_user_fns_id", "fns_receipts", ["user_id", "fns_id"])


def downgrade():
    op.drop_constraint("uq_fns_receipts_user_fns_id", "fns_receipts", type_="unique")
