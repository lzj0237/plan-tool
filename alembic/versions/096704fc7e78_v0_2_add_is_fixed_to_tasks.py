"""v0.2 add is_fixed to tasks

Revision ID: 096704fc7e78
Revises: 413a3d73a3eb
Create Date: 2026-03-26 10:01:09.921197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '096704fc7e78'
down_revision: Union[str, Sequence[str], None] = '413a3d73a3eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tasks", sa.Column("is_fixed", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "is_fixed")
