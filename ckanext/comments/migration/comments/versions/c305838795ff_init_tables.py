"""empty message

Revision ID: c305838795ff
Revises: acd1862c2e17
Create Date: 2024-10-07 09:20:07.820195

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'c305838795ff'
down_revision = 'acd1862c2e17'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("comments_comments")]

    if "author_email" not in columns:
        op.add_column(
            "comments_comments",
            sa.Column("author_email", sa.UnicodeText, nullable=False)
        )
    else:
        print("Spalte 'author_email' existiert bereits – wird nicht erneut hinzugefügt.")


def downgrade():
    op.drop_column("comments_comments", "author_email")