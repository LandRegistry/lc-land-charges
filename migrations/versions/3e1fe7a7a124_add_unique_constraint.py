"""Add unique constraint:


Revision ID: 3e1fe7a7a124
Revises: 216e3942ea3
Create Date: 2016-01-07 07:49:29.404090

"""

# revision identifiers, used by Alembic.
revision = '3e1fe7a7a124'
down_revision = '216e3942ea3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_unique_constraint("uq_registration_ref", "register", ["registration_no", "date"])


def downgrade():
    op.drop_constraint("uq_registration_ref", "register")
