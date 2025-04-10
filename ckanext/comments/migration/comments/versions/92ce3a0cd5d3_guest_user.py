"""empty message

Revision ID: 92ce3a0cd5d3
Revises: c305838795ff
Create Date: 2025-04-09 15:17:19.213516

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92ce3a0cd5d3'
down_revision = 'c305838795ff'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "comments_comments",
        sa.Column("guest_user", sa.UnicodeText, nullable=True)
    )


def downgrade():
    op.drop_column("comments_comments", "guest_user")
