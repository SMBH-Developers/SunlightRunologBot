"""comment

Revision ID: 80e3606aefdd
Revises: 7453e8f28c13
Create Date: 2024-03-24 17:21:08.170169

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80e3606aefdd'
down_revision = '7453e8f28c13'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('got_52h_autosending', sa.TIMESTAMP(), nullable=True))
    op.add_column('users', sa.Column('got_76h_autosending', sa.TIMESTAMP(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'got_76h_autosending')
    op.drop_column('users', 'got_52h_autosending')
    # ### end Alembic commands ###
