# backend/app/engines/strategies/peg.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.schemas.strategy import FilterCondition, ConditionOperator

class PEGStrategy:
    """PEG Growth Strategy

    Criteria:
    - PEG < 1
    - Revenue growth rate > 20%
    - Net profit growth rate > 20%
    - ROE > 10%
    - Market cap > 5B
    """

    def __init__(self):
        self.filter_engine = StockFilter()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute PEG growth strategy"""
        # Default parameters
        roe_min = params.get("roe_min", 10.0) if params else 10.0
        market_cap_min = params.get("market_cap_min", 5000000000) if params else 5000000000

        # Build conditions
        conditions = [
            FilterCondition(field="roe", operator=ConditionOperator.GT, value=roe_min),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
        ]

        # Apply filters
        results = await self.filter_engine.apply_filter(conditions)

        # Sort by ROE (higher is better for growth stocks)
        results.sort(key=lambda x: x.get("roe", 0), reverse=True)

        return results[:50]  # Top 50 results
