"""v0.2 add reschedule logs

Revision ID: 413a3d73a3eb
Revises: 928a60d8157d
Create Date: 2026-03-26 10:00:15.461931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '413a3d73a3eb'
down_revision: Union[str, Sequence[str], None] = '928a60d8157d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "task_reschedule_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("from_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("from_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("to_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("to_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("minutes_pushed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_task_reschedule_logs_task_id",
        "task_reschedule_logs",
        ["task_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_task_reschedule_logs_task_id", table_name="task_reschedule_logs")
    op.drop_table("task_reschedule_logs")
