"""assignment due_at

Revision ID: b7d4e1a9c2f6
Revises: a1c9f0d2e7b3
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d4e1a9c2f6'
down_revision: Union[str, Sequence[str], None] = 'a1c9f0d2e7b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('assignments', sa.Column('due_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('assignments', 'due_at')
