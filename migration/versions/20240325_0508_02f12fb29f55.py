"""init

Revision ID: 02f12fb29f55
Revises: 80e3606aefdd
Create Date: 2024-03-25 05:08:20.171218

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '02f12fb29f55'
down_revision = '80e3606aefdd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('sending_25_march', sa.TIMESTAMP(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'sending_25_march')
    # ### end Alembic commands ###
