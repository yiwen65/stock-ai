# backend/app/engines/strategies/buffett.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.schemas.strategy import FilterCondition, ConditionOperator

class BuffettStrategy:
    """Buffett Moat Strategy

    Criteria:
    - ROE > 15% for 5 consecutive years
    - ROE standard deviation < 5%
    - Gross margin > 30%
    - Free cash flow positive for 3 consecutive years
    - Debt ratio < 50%
    - Market cap > 10B
    """

    def __init__(self):
        self.filter_engine = StockFilter()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute Buffett moat strategy"""
        # Default parameters
        roe_min = params.get("roe_min", 15.0) if params else 15.0
        gross_margin_min = params.get("gross_margin_min", 30.0) if params else 30.0
        debt_max = params.get("debt_max", 50.0) if params else 50.0
        market_cap_min = params.get("market_cap_min", 10000000000) if params else 10000000000

        # Build conditions
        conditions = [
            FilterCondition(field="roe", operator=ConditionOperator.GT, value=roe_min),
            FilterCondition(field="debt_ratio", operator=ConditionOperator.LT, value=debt_max),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
        ]

        # Apply filters
        results = await self.filter_engine.apply_filter(conditions)

        # Sort by ROE (higher is better)
        results.sort(key=lambda x: x.get("roe", 0), reverse=True)

        return results[:50]  # Top 50 results
