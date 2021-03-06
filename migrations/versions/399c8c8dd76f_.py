"""empty message

Revision ID: 399c8c8dd76f
Revises: 
Create Date: 2020-08-17 13:06:58.652838

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '399c8c8dd76f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lottery_overview',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lottery_id', postgresql.UUID(), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('rotation_number', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lottery_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('points', sa.Integer(), nullable=True),
    sa.Column('final_ranking', sa.Integer(), nullable=True),
    sa.Column('lottery_id', postgresql.UUID(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('lottery_results')
    op.drop_table('lottery_overview')
    # ### end Alembic commands ###
