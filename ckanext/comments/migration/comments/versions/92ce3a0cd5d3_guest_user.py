"""empty message

Revision ID: 92ce3a0cd5d3
Revises: c305838795ff
Create Date: 2025-04-09 15:17:19.213516

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '92ce3a0cd5d3'
down_revision = 'c305838795ff'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("comments_comments")]

    if "guest_user" not in columns:
        op.add_column(
            "comments_comments",
            sa.Column("guest_user", sa.UnicodeText, nullable=True)
        )
    else:
        print("Spalte 'guest_user' existiert bereits – wird nicht erneut hinzugefügt.")


def downgrade():
    op.drop_column("comments_comments", "guest_user")

