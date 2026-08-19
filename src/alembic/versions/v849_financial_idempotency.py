"""Financial idempotency and duplicate bank transaction protection."""
from alembic import op
import sqlalchemy as sa

revision = "v849_financial_idempotency"
down_revision = "v842_security_cleanup"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    payment_cols = {c["name"] for c in insp.get_columns("payments")}
    payment_indexes = {idx.get("name") for idx in insp.get_indexes("payments")}
    if "idempotency_key" not in payment_cols:
        op.add_column("payments", sa.Column("idempotency_key", sa.String(255), nullable=True))
    if "ix_payments_idempotency_key" not in payment_indexes:
        op.create_index("ix_payments_idempotency_key", "payments", ["idempotency_key"], unique=True)
    tx_cols = {c["name"] for c in insp.get_columns("transactions")}
    if "bank_transaction_id" in tx_cols:
        constraints = {c.get("name") for c in insp.get_unique_constraints("transactions")}
        if "uq_transactions_user_bank_id" not in constraints:
            op.create_unique_constraint("uq_transactions_user_bank_id", "transactions", ["user_id", "bank_transaction_id"])

def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    constraints = {c.get("name") for c in insp.get_unique_constraints("transactions")}
    if "uq_transactions_user_bank_id" in constraints:
        op.drop_constraint("uq_transactions_user_bank_id", "transactions", type_="unique")
    if "ix_payments_idempotency_key" in {idx.get("name") for idx in insp.get_indexes("payments")}:
        op.drop_index("ix_payments_idempotency_key", table_name="payments")
    if "idempotency_key" in {c["name"] for c in insp.get_columns("payments")}:
        op.drop_column("payments", "idempotency_key")
