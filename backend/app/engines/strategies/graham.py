# backend/app/engines/strategies/graham.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.schemas.strategy import FilterCondition, ConditionOperator

class GrahamStrategy:
    """Graham Value Investing Strategy

    Criteria:
    - PE < 15
    - PB < 2
    - Debt Ratio < 60%
    - Market Cap > 5B (risk filter)
    """

    def __init__(self):
        self.filter_engine = StockFilter()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute Graham value strategy"""
        # Default parameters
        pe_max = params.get("pe_max", 15.0) if params else 15.0
        pb_max = params.get("pb_max", 2.0) if params else 2.0
        debt_max = params.get("debt_max", 60.0) if params else 60.0
        market_cap_min = params.get("market_cap_min", 5000000000) if params else 5000000000

        # Build conditions
        conditions = [
            FilterCondition(field="pe", operator=ConditionOperator.LT, value=pe_max),
            FilterCondition(field="pb", operator=ConditionOperator.LT, value=pb_max),
            FilterCondition(field="debt_ratio", operator=ConditionOperator.LT, value=debt_max),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
        ]

        # Apply filters
        results = await self.filter_engine.apply_filter(conditions)

        # Sort by PE (lower is better)
        results.sort(key=lambda x: x.get("pe", 999))

        return results[:50]  # Top 50 results
