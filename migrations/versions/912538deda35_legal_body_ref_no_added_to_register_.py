"""legal body ref no added to register details

Revision ID: 912538deda35
Revises: 13a903d0a807
Create Date: 2016-02-19 12:15:09.963623

"""

# revision identifiers, used by Alembic.
revision = '912538deda35'
down_revision = '13a903d0a807'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('legal_body_ref_no', sa.Unicode()))


def downgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('legal_body_ref_no')