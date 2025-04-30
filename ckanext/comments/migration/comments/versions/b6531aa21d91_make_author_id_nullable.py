"""make author_id nullable

Revision ID: b6531aa21d91
Revises: 92ce3a0cd5d3
Create Date: 2025-04-30 20:53:20.580103

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6531aa21d91'
down_revision = '92ce3a0cd5d3'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('comments_comments', 'author_id',
                    existing_type=sa.Text(),
                    nullable=True)

def downgrade():
    op.alter_column('comments_comments', 'author_id',
                    existing_type=sa.Text(),
                    nullable=False)
