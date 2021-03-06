"""empty message

Revision ID: 03ac007a81c3
Revises: 1948a3f65561
Create Date: 2020-08-18 00:14:30.417866

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '03ac007a81c3'
down_revision = '1948a3f65561'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('points',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('points_one', sa.Integer(), nullable=True),
    sa.Column('points_two', sa.Integer(), nullable=True),
    sa.Column('points_three', sa.Integer(), nullable=True),
    sa.Column('points_four', sa.Integer(), nullable=True),
    sa.Column('points_five', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('points')
    # ### end Alembic commands ###
