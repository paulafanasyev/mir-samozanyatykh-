"""Tax/financial integrity constraints.

Revision ID: v850_tax_financial_integrity
Revises: v849_financial_idempotency
"""
from alembic import op
import sqlalchemy as sa

revision = "v850_tax_financial_integrity"
down_revision = "v849_financial_idempotency"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tx_cols = {c["name"] for c in insp.get_columns("transactions")}
    if "counterparty_type" not in tx_cols:
        op.add_column("transactions", sa.Column("counterparty_type", sa.String(length=20), nullable=True))
    if "ix_transactions_user_counterparty_type" not in {i.get("name") for i in insp.get_indexes("transactions")}:
        op.create_index("ix_transactions_user_counterparty_type", "transactions", ["user_id", "counterparty_type"])
    if "uq_tax_reports_user_period" not in {i.get("name") for i in insp.get_indexes("tax_reports")}:
        op.create_index("uq_tax_reports_user_period", "tax_reports", ["user_id", "report_type", "period_start", "period_end"], unique=True)
    if "ck_transactions_amount_positive" not in {c.get("name") for c in insp.get_check_constraints("transactions")}:
        op.create_check_constraint("ck_transactions_amount_positive", "transactions", "amount > 0")


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "ix_transactions_user_counterparty_type" in {i.get("name") for i in insp.get_indexes("transactions")}:
        op.drop_index("ix_transactions_user_counterparty_type", table_name="transactions")
    if "ck_transactions_amount_positive" in {c.get("name") for c in insp.get_check_constraints("transactions")}:
        op.drop_constraint("ck_transactions_amount_positive", "transactions", type_="check")
    if "counterparty_type" in {c["name"] for c in insp.get_columns("transactions")}:
        op.drop_column("transactions", "counterparty_type")
    if "uq_tax_reports_user_period" in {i.get("name") for i in insp.get_indexes("tax_reports")}:
        op.drop_index("uq_tax_reports_user_period", table_name="tax_reports")
