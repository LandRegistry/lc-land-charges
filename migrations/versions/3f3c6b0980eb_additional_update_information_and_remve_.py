"""Additional update information and remove counties table

Revision ID: 3f3c6b0980eb
Revises: 273e31d6ab30
Create Date: 2016-03-04 13:10:17.470979

"""

# revision identifiers, used by Alembic.
revision = '3f3c6b0980eb'
down_revision = '273e31d6ab30'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('amend_info_type', sa.String()))
        batch_op.add_column(sa.Column('amend_info_details', sa.String()))

    op.drop_table('counties')


def downgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('amend_info_type')
        batch_op.drop_column('amend_info_details')

    op.create_table('counties',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('welsh_name', sa.String(), nullable=True)
                    )
