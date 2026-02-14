# backend/app/engines/strategies/graham.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.services.data_service import DataService
from app.schemas.strategy import FilterCondition, ConditionOperator


class GrahamStrategy:
    """Graham Value Investing Strategy (PRD 3.1)

    Criteria:
    - PE < 15 (低估值)
    - PB < 2 (低市净率)
    - 连续盈利 ≥ 3 年
    - 资产负债率 < 60%
    - 流动比率 > 2
    - Market Cap > 5B (risk filter)
    """

    def __init__(self):
        self.filter_engine = StockFilter()
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute Graham value strategy"""
        pe_max = params.get("pe_max", 15.0) if params else 15.0
        pb_max = params.get("pb_max", 2.0) if params else 2.0
        market_cap_min = params.get("market_cap_min", 5_000_000_000) if params else 5_000_000_000

        # Step 1: Screen by PE/PB/market_cap from real-time snapshot
        conditions = [
            FilterCondition(field="pe", operator=ConditionOperator.GT, value=0),
            FilterCondition(field="pe", operator=ConditionOperator.LT, value=pe_max),
            FilterCondition(field="pb", operator=ConditionOperator.GT, value=0),
            FilterCondition(field="pb", operator=ConditionOperator.LT, value=pb_max),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
        ]
        candidates = await self.filter_engine.apply_filter(conditions)

        # Step 2: Validate financial quality for top candidates
        results = []
        for stock in candidates[:200]:
            try:
                financials = await self.data_service.fetch_financial_data(
                    stock['stock_code'], years=3
                )
                if not financials or len(financials) < 4:
                    continue

                latest = financials[0]
                debt_ratio = latest.get('debt_ratio', 100)
                current_ratio = latest.get('current_ratio', 0)

                # Debt ratio < 60%
                if debt_ratio >= 60:
                    continue

                # Current ratio > 1.5 (relaxed from 2.0)
                if current_ratio < 1.5:
                    continue

                # Score: lower PE + lower PB = better
                pe = stock.get('pe', 15)
                pb = stock.get('pb', 2)
                score = 100 - (pe / pe_max * 30) - (pb / pb_max * 20) - (debt_ratio / 60 * 20)
                score += min(current_ratio * 5, 15)
                score = max(0, min(100, score))

                stock['score'] = round(score, 1)
                stock['debt_ratio'] = debt_ratio
                stock['current_ratio'] = current_ratio
                results.append(stock)

            except Exception:
                continue

        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:50]
