"""Add court/INS details fields

Revision ID: 3784951a9d3
Revises: 18e886734a7
Create Date: 2015-08-21 12:50:37.081056

"""

# revision identifiers, used by Alembic.
revision = '3784951a9d3'
down_revision = '18e886734a7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('legal_body', sa.Unicode()))
        batch_op.add_column(sa.Column('legal_body_ref', sa.Unicode()))


def downgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('legal_body')
        batch_op.drop_column('legal_body_ref')
