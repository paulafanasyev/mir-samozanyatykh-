"""Initial schema baseline for Mir Samozanykh.

Revision ID: render_v84
Revises: <base>

This migration is intentionally the complete schema baseline.  Older releases
created tables with SQLAlchemy ``create_all`` during application startup, which
made a fresh production deployment unable to run Alembic because later
migrations referenced tables that did not exist.  The baseline now creates the
entire current model metadata once; later revisions only apply incremental
changes and are written to be idempotent against this baseline.
"""
from alembic import op

from app.core.database import Base
from app import models  # noqa: F401 - registers all models on Base.metadata

revision = "render_v84"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade():
    raise RuntimeError("Baseline downgrade is intentionally disabled: dropping the production schema would destroy all data. Restore a verified backup instead.")
