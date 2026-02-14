"""add_performance_indexes

Revision ID: a81999e907ce
Revises: e619d745d6f6
Create Date: 2026-02-14 02:42:03.726850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a81999e907ce'
down_revision: Union[str, None] = 'e619d745d6f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Indexes already created in their respective table migrations; no-op.
    pass


def downgrade() -> None:
    pass
