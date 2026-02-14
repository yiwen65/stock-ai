"""merge_heads

Revision ID: 1a727be157c0
Revises: a81999e907ce, d70482335f8e
Create Date: 2026-02-14 15:58:07.898739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a727be157c0'
down_revision: Union[str, None] = ('a81999e907ce', 'd70482335f8e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
