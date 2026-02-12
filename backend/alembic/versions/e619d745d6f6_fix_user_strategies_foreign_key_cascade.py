"""fix user_strategies foreign key cascade

Revision ID: e619d745d6f6
Revises: c60473224f7d
Create Date: 2026-02-13 02:22:08.596419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e619d745d6f6'
down_revision: Union[str, None] = 'c60473224f7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing foreign key constraint
    op.drop_constraint('user_strategies_user_id_fkey', 'user_strategies', type_='foreignkey')

    # Recreate with CASCADE
    op.create_foreign_key(
        'user_strategies_user_id_fkey',
        'user_strategies', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop CASCADE foreign key
    op.drop_constraint('user_strategies_user_id_fkey', 'user_strategies', type_='foreignkey')

    # Recreate without CASCADE
    op.create_foreign_key(
        'user_strategies_user_id_fkey',
        'user_strategies', 'users',
        ['user_id'], ['id']
    )
