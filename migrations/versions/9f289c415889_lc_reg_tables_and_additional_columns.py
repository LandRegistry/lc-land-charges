"""lc reg tables and additional columns

Revision ID: 9f289c415889
Revises: 3e1fe7a7a124
Create Date: 2016-01-13 10:37:08.110501

"""

# revision identifiers, used by Alembic.
revision = '9f289c415889'
down_revision = '3e1fe7a7a124'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('county',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('name', sa.Unicode(), nullable=False)
                    )

    op.create_table('detl_county_rel',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('county_id', sa.Integer(), sa.ForeignKey('county.id'), nullable=False),
                    sa.Column('details_id', sa.Integer(), sa.ForeignKey('register_details.id'), nullable=False)
                    )

    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('district', sa.Unicode()))
        batch_op.add_column(sa.Column('short_description', sa.Unicode()))
        batch_op.add_column(sa.Column('additional_info', sa.Unicode()))

    with op.batch_alter_table("party_name") as batch_op:
        batch_op.add_column(sa.Column('name_type_ind', sa.Unicode()))
        batch_op.add_column(sa.Column('company_name', sa.Unicode()))
        batch_op.add_column(sa.Column('local_authority_name', sa.Unicode()))
        batch_op.add_column(sa.Column('local_authority_area', sa.Unicode()))
        batch_op.add_column(sa.Column('other_name', sa.Unicode()))


def downgrade():
    op.drop_table('county')
    op.drop_table('detl_county_rel')

    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('district')
        batch_op.drop_column('short_description')
        batch_op.drop_column('additional_info')

    with op.batch_alter_table("party_name") as batch_op:
        batch_op.drop_column('name_type_ind')
        batch_op.drop_column('company_name')
        batch_op.drop_column('local_authority_name')
        batch_op.drop_column('local_authority_area')
        batch_op.drop_column('other_name')