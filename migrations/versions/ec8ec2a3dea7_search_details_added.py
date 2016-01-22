"""search details added

Revision ID: ec8ec2a3dea7
Revises: d773e0a1af3d
Create Date: 2016-01-22 10:35:02.537448

"""

# revision identifiers, used by Alembic.
revision = 'ec8ec2a3dea7'
down_revision = 'd773e0a1af3d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('search_details')

    op.create_table('search_details',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('request_id', sa.Integer(), sa.ForeignKey('request.id'), nullable=False),
                    sa.Column('search_timestamp', sa.TIMESTAMP(), nullable=False),
                    sa.Column('type', sa.Unicode(), sa.Enum('Full', 'Banks', name='type'), nullable=False),
                    sa.Column('counties', sa.Unicode(), nullable=True)
                    )

    op.create_table('search_name',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('details_id', sa.Integer(), sa.ForeignKey('search_details.id'), nullable=False),
                    sa.Column('name_type', sa.Unicode(), nullable=False),
                    sa.Column('forenames', sa.Unicode(), nullable=True),
                    sa.Column('surname', sa.Unicode(), nullable=True),
                    sa.Column('complex_name', sa.Unicode(), nullable=True),
                    sa.Column('complex_number', sa.Integer(), nullable=True),
                    sa.Column('company_name', sa.Unicode(), nullable=True),
                    sa.Column('local_authority_name', sa.Unicode(), nullable=True),
                    sa.Column('local_authority_area', sa.Unicode(), nullable=True),
                    sa.Column('other_name', sa.Unicode(), nullable=True),
                    sa.Column('year_search_from', sa.Unicode(), nullable=True),
                    sa.Column('year_search_to', sa.Unicode(), nullable=True)
                    )


def downgrade():
    op.drop_table('search_details')
    op.drop_table('search_name')