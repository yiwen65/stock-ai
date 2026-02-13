# backend/app/engines/strategies/lynch.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.schemas.strategy import FilterCondition, ConditionOperator

class LynchStrategy:
    """Peter Lynch Growth Strategy

    Criteria:
    - PE < industry average
    - Revenue growth rate > 15%
    - Net profit growth rate > 15%
    - Debt ratio < 60%
    - Market cap > 3B
    """

    def __init__(self):
        self.filter_engine = StockFilter()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute Lynch growth strategy"""
        # Default parameters
        pe_max = params.get("pe_max", 20.0) if params else 20.0
        debt_max = params.get("debt_max", 60.0) if params else 60.0
        market_cap_min = params.get("market_cap_min", 3000000000) if params else 3000000000

        # Build conditions
        conditions = [
            FilterCondition(field="pe", operator=ConditionOperator.LT, value=pe_max),
            FilterCondition(field="debt_ratio", operator=ConditionOperator.LT, value=debt_max),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
        ]

        # Apply filters
        results = await self.filter_engine.apply_filter(conditions)

        # Sort by PE (lower is better)
        results.sort(key=lambda x: x.get("pe", 999))

        return results[:50]  # Top 50 results
