"""add extras column to comments table

Revision ID: acd1862c2e17
Revises: 910f3d575038
Create Date: 2023-10-23 20:29:49.771688

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "acd1862c2e17"
down_revision = "910f3d575038"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = [col["name"] for col in inspector.get_columns("comments_comments")]
    if "extras" not in columns:
        op.add_column(
            "comments_comments",
            sa.Column("extras", JSONB, nullable=False, server_default="{}"),
        )
    else:
        print("Spalte 'extras' existiert bereits – wird nicht erneut hinzugefügt.")


def downgrade():
    op.drop_column("comments_comments", "extras")
