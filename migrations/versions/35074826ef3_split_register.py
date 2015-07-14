"""split register

Revision ID: 35074826ef3
Revises: 31cae288f4e
Create Date: 2015-07-13 11:51:48.169462

"""

# revision identifiers, used by Alembic.
revision = '35074826ef3'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    # FK constraints make it tricky to make this change. Therefore, burn the whole thing down and redo...
    op.create_table('party_name',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('party_name', sa.Unicode()),
                    sa.Column('gender', sa.CHAR()),
                    sa.Column('forename', sa.Unicode()),
                    sa.Column('middle_names', sa.Unicode()),
                    sa.Column('surname', sa.Unicode()),
                    sa.Column('alias_name', sa.Boolean())
                    )

    op.create_table('ins_bankruptcy_request',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('request_data', postgresql.JSON(), nullable=False))

    op.create_table('request',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('key_number', sa.String()),
                    sa.Column('application_type', sa.Enum('PAB', 'WOB', name='application_type')),
                    sa.Column('application_reference', sa.String()),
                    sa.Column('application_date', sa.Date()),
                    sa.Column('ins_request_id', sa.Integer(), sa.ForeignKey('ins_bankruptcy_request.id')))

    op.create_table('audit_log',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('request_id', sa.Integer(), sa.ForeignKey('request.id'), nullable=False),
                    sa.Column('activity_code', sa.Enum('Capture', 'View', 'Register', name='activity'), nullable=False),
                    sa.Column('activity_time', sa.DateTime(), nullable=False),
                    sa.Column('actor_id', sa.Unicode(), nullable=False),
                    sa.Column('ip_address', postgresql.INET()),
                    sa.Column('application_ref', sa.Integer()))

    op.create_table('register_details',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('request_id', sa.Integer(), sa.ForeignKey('request.id')),
                    sa.Column('registration_date', sa.Date(), nullable=False),
                    sa.Column('application_type', sa.Enum('PAB', 'WOB', name='application_type_2')), #  TODO: this is a hack.
                    sa.Column('bankruptcy_date', sa.Date(), nullable=False))

    op.create_table('register',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('registration_no', sa.Integer(), nullable=False, unique=True),
                    sa.Column('debtor_reg_name_id', sa.Integer(), sa.ForeignKey('party_name.id')),
                    sa.Column('details_id', sa.Integer(), sa.ForeignKey('register_details.id'))
                    )

    op.create_table('migration_status',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('register_id', sa.Integer(), sa.ForeignKey('register.id'), nullable=False),
                    sa.Column('original_regn_no', sa.Integer()),
                    sa.Column('migration_complete', sa.Boolean, nullable=False, default=False),
                    sa.Column('extra_data', postgresql.JSON()))

    op.create_table('party',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('register_detl_id', sa.Integer(), sa.ForeignKey('register_details.id'), nullable=False),
                    sa.Column('party_type', sa.Enum('Customer', 'Creditor', 'Debtor', name='party_type')),
                    sa.Column('occupation', sa.Unicode()),
                    sa.Column('date_of_birth', sa.Date()),
                    sa.Column('residence_withheld', sa.Boolean()),
                    )

    op.create_table('party_name_rel',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('party_name_id', sa.Integer(), sa.ForeignKey("party_name.id"), nullable=False),
                    sa.Column('party_id', sa.Integer(), sa.ForeignKey("party.id"), nullable=False)
                    )

    op.create_table('party_trading',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('party_id', sa.Integer(), sa.ForeignKey('party.id')),
                    sa.Column('trading_name', sa.Unicode()))

    op.create_table('address_detail',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('line_1', sa.Unicode()),
                    sa.Column('line_2', sa.Unicode()),
                    sa.Column('line_3', sa.Unicode()),
                    sa.Column('line_4', sa.Unicode()),
                    sa.Column('line_5', sa.Unicode()),
                    sa.Column('line_6', sa.Unicode()),
                    sa.Column('country_id', sa.String()))

    op.create_table('address',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('address_type', sa.Enum('Debtor Residence', 'Debtor Owned', 'Debtor Business', 'Customer',
                                                      'Investment', name='address_type')),
                    sa.Column('address_string', sa.Unicode()),
                    sa.Column('detail_id', sa.Integer(), sa.ForeignKey('address_detail.id'), nullable=False))

    op.create_table('party_address',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('address_id', sa.Integer(), sa.ForeignKey('address.id'), nullable=False),
                    sa.Column('party_id', sa.Integer(), sa.ForeignKey('party.id'), nullable=False))


def downgrade():
    op.drop_table('party_address')
    op.drop_table('address')
    op.drop_table('address_detail')
    op.drop_table('party_trading')
    op.drop_table('party_name_rel')
    op.drop_table('party')
    op.drop_table('migration_status')
    op.drop_table('register')
    op.drop_table('register_details')
    op.drop_table('audit_log')
    op.drop_table('request')
    op.drop_table('ins_bankruptcy_request')
    op.drop_table('party_name')

    # At this point give up trying to delete the types in a database-agnostic manner and just issue DDL...
    op.execute("DROP TYPE address_type")
    op.execute("DROP TYPE activity")
    op.execute("DROP TYPE party_type")
    op.execute("DROP TYPE application_type")
    op.execute("DROP TYPE application_type_2")
