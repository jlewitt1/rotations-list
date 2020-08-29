"""empty message

Revision ID: ed2b6252983c
Revises: d1cab20eebd2
Create Date: 2020-08-29 18:07:18.801601

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed2b6252983c'
down_revision = 'd1cab20eebd2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lottery_overview', sa.Column('organization', sa.String(length=1000), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lottery_overview', 'organization')
    # ### end Alembic commands ###
