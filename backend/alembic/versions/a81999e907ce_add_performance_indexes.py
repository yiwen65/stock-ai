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
    # Stock table indexes for filtering and sorting
    op.create_index('idx_stocks_industry', 'stocks', ['industry'])
    op.create_index('idx_stocks_market_cap', 'stocks', ['market_cap'])
    op.create_index('idx_stocks_pe_ttm', 'stocks', ['pe_ttm'])
    op.create_index('idx_stocks_pb', 'stocks', ['pb'])

    # Stock financials indexes for filtering
    op.create_index('idx_financials_stock_code', 'stock_financials', ['stock_code'])
    op.create_index('idx_financials_roe', 'stock_financials', ['roe'])
    op.create_index('idx_financials_report_date', 'stock_financials', ['report_date'])

    # Strategy executions indexes for user queries
    op.create_index(
        'idx_executions_user_time',
        'strategy_executions',
        ['user_id', 'executed_at']
    )
    op.create_index('idx_executions_strategy_id', 'strategy_executions', ['strategy_id'])

    # User strategies indexes
    op.create_index('idx_strategies_user_id', 'user_strategies', ['user_id'])
    op.create_index('idx_strategies_created_at', 'user_strategies', ['created_at'])


def downgrade() -> None:
    # Drop all indexes in reverse order
    op.drop_index('idx_strategies_created_at')
    op.drop_index('idx_strategies_user_id')
    op.drop_index('idx_executions_strategy_id')
    op.drop_index('idx_executions_user_time')
    op.drop_index('idx_financials_report_date')
    op.drop_index('idx_financials_roe')
    op.drop_index('idx_financials_stock_code')
    op.drop_index('idx_stocks_pb')
    op.drop_index('idx_stocks_pe_ttm')
    op.drop_index('idx_stocks_market_cap')
    op.drop_index('idx_stocks_industry')
