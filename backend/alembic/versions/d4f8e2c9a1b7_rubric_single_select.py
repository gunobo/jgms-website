"""rubric single-select grading (rename checked_item_ids to selected_item_ids)

Revision ID: d4f8e2c9a1b7
Revises: b7d4e1a9c2f6
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f8e2c9a1b7'
down_revision: Union[str, Sequence[str], None] = 'b7d4e1a9c2f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('grades') as batch_op:
        batch_op.alter_column(
            'checked_item_ids', new_column_name='selected_item_ids', existing_type=sa.JSON()
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('grades') as batch_op:
        batch_op.alter_column(
            'selected_item_ids', new_column_name='checked_item_ids', existing_type=sa.JSON()
        )
