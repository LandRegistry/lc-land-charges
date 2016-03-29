"""Add Indices

Revision ID: c0f5e8607e37
Revises: 2c414175786e
Create Date: 2016-03-29 12:46:00.454751

"""

# revision identifiers, used by Alembic.
revision = 'c0f5e8607e37'
down_revision = '2c414175786e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('register_details_id_ix', 'register', ['details_id'])
    op.create_index('register_debtor_id_ix', 'register', ['debtor_reg_name_id'])
    op.create_index('detl_county_details_id_ix', 'detl_county_rel', ['details_id'])
    op.create_index('reg_details_request_id_ix', 'register_details', ['request_id'])
    op.create_index('party_address_address_id_ix', 'party_address', ['address_id'])
    op.create_index('party_address_party_id_ix', 'party_address', ['party_id'])
    op.create_index('address_detail_id_ix', 'address', ['detail_id'])
    op.create_index('party_detail_id_ix', 'party', ['register_detl_id'])
    op.create_index('party_name_rel_party_name_id_ix', 'party_name_rel', ['party_name_id'])
    op.create_index('party_name_rel_party_id_ix', 'party_name_rel', ['party_id'])
    op.create_index('party_trading_party_id_ix', 'party_trading', ['party_id'])

 #   op.create_index('ik_test', 't1', ['foo', 'bar'])
#create_index(index_name, table_name, columns, schema=None, unique=False, **kw)

def downgrade():
    op.drop_index('register_details_id_ix')
    op.drop_index('register_debtor_id_ix')
    op.drop_index('detl_county_details_id_ix')
    op.drop_index('reg_details_request_id_ix')
    op.drop_index('party_address_address_id_ix')
    op.drop_index('party_address_party_id_ix')
    op.drop_index('address_detail_id_ix')
    op.drop_index('party_detail_id_ix')
    op.drop_index('party_name_rel_party_name_id_ix')
    op.drop_index('party_name_rel_party_id_ix')
    op.drop_index('party_trading_party_id_ix')
