# backend/app/engines/strategies/rs_momentum.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.services.data_service import DataService
from app.schemas.strategy import FilterCondition, ConditionOperator


class RSMomentumStrategy:
    """RS Relative Strength Momentum Strategy

    Criteria:
    - 60-day return in top percentile (strong relative strength)
    - Volume ratio > 1 (active trading)
    - Market cap > 3B (liquidity)
    - YTD return positive
    """

    def __init__(self):
        self.filter_engine = StockFilter()
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute RS momentum strategy"""
        min_change_60d = params.get("min_change_60d", 15.0) if params else 15.0
        market_cap_min = params.get("market_cap_min", 3_000_000_000) if params else 3_000_000_000

        # Screen by 60-day return + market cap + volume ratio
        conditions = [
            FilterCondition(field="change_60d", operator=ConditionOperator.GT, value=min_change_60d),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
            FilterCondition(field="volume_ratio", operator=ConditionOperator.GT, value=0.8),
            FilterCondition(field="change_ytd", operator=ConditionOperator.GT, value=0),
        ]
        candidates = await self.filter_engine.apply_filter(conditions)

        # Score based on momentum strength
        results = []
        for stock in candidates[:200]:
            change_60d = stock.get("change_60d", 0)
            change_ytd = stock.get("change_ytd", 0)
            volume_ratio = stock.get("volume_ratio", 1)
            turnover = stock.get("turnover_rate", 0)

            # Composite score: 60d momentum + YTD momentum + volume activity
            score = min(change_60d * 1.5, 50) + min(change_ytd * 0.5, 25) + min(volume_ratio * 5, 15) + min(turnover * 2, 10)
            score = max(0, min(100, score))

            stock["score"] = round(score, 1)
            stock["risk_level"] = "high" if change_60d > 50 else "medium"
            results.append(stock)

        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:50]
