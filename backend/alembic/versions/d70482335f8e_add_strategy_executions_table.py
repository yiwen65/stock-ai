"""Add strategy_executions table

Revision ID: d70482335f8e
Revises: c60473224f7d
Create Date: 2026-02-15 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd70482335f8e'
down_revision: Union[str, None] = 'c60473224f7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('strategy_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=False),
        sa.Column('result_snapshot', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['strategy_id'], ['user_strategies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_strategy_executions_strategy_id'), 'strategy_executions', ['strategy_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_strategy_executions_strategy_id'), table_name='strategy_executions')
    op.drop_table('strategy_executions')
