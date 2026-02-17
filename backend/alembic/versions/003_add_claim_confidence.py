"""Add confidence column to claims table

Revision ID: 003
Revises: 002
Create Date: 2026-02-17
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("claims", sa.Column("confidence", sa.Float(), server_default="0.5", nullable=False))


def downgrade():
    op.drop_column("claims", "confidence")
