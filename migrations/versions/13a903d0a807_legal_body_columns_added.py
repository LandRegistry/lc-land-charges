"""legal body columns added

Revision ID: 13a903d0a807
Revises: 9efd4a33d2f6
Create Date: 2016-02-19 09:20:07.241821

"""

# revision identifiers, used by Alembic.
revision = '13a903d0a807'
down_revision = '9efd4a33d2f6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('legal_body', sa.Unicode()))
        batch_op.add_column(sa.Column('legal_body_ref_year', sa.Integer()))


def downgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('legal_body')
        batch_op.drop_column('legal_body_ref_year')