"""roster sheet

Revision ID: a1c9f0d2e7b3
Revises: 1eb108b4fc5b
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c9f0d2e7b3'
down_revision: Union[str, Sequence[str], None] = '1eb108b4fc5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('roster_sheet',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('sheet_id', sa.String(length=200), nullable=True),
    sa.Column('sheet_tab', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('roster_sheet')
