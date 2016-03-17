"""Remove legal body columns

Revision ID: f82a88ad5d9b
Revises: a906fae12e18
Create Date: 2016-03-17 11:04:42.680793

"""

# revision identifiers, used by Alembic.
revision = 'f82a88ad5d9b'
down_revision = 'a906fae12e18'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('legal_body')
        batch_op.drop_column('legal_body_ref_no')
        batch_op.drop_column('legal_body_ref_year')


def downgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('legal_body', sa.Unicode()))
        batch_op.add_column(sa.Column('legal_body_ref_no', sa.Unicode()))
        batch_op.add_column(sa.Column('legal_body_ref_year', sa.Integer()))
