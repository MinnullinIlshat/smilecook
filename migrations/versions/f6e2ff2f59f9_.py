"""empty message

Revision ID: f6e2ff2f59f9
Revises: 503df6d8f7e0
Create Date: 2023-03-19 07:41:35.399808

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6e2ff2f59f9'
down_revision = '503df6d8f7e0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipe', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ingredients', sa.String(length=600), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipe', schema=None) as batch_op:
        batch_op.drop_column('ingredients')

    # ### end Alembic commands ###
