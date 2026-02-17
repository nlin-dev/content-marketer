"""Update ClaimCategory enum to FRUZAQLA-specific categories

Revision ID: 002
Revises: 001
Create Date: 2026-02-17
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE claims ALTER COLUMN category TYPE TEXT")
    op.execute("DROP TYPE IF EXISTS claimcategory")
    op.execute(
        "CREATE TYPE claimcategory AS ENUM "
        "('efficacy_os', 'efficacy_pfs', 'safety', 'moa', 'dosing', "
        "'qol', 'subgroups', 'dcr', 'unmet_need', 'positioning')"
    )
    op.execute(
        "ALTER TABLE claims ALTER COLUMN category "
        "TYPE claimcategory USING category::claimcategory"
    )


def downgrade():
    op.execute("ALTER TABLE claims ALTER COLUMN category TYPE TEXT")
    op.execute("DROP TYPE IF EXISTS claimcategory")
    op.execute(
        "CREATE TYPE claimcategory AS ENUM "
        "('efficacy', 'safety', 'mechanism', 'dosing', 'indication', "
        "'survival', 'response_rate', 'biomarker', 'combination', 'quality_of_life')"
    )
    op.execute(
        "ALTER TABLE claims ALTER COLUMN category "
        "TYPE claimcategory USING category::claimcategory"
    )
