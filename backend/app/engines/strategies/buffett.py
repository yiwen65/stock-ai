# backend/app/engines/strategies/buffett.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.services.data_service import DataService
from app.schemas.strategy import FilterCondition, ConditionOperator


class BuffettStrategy:
    """Buffett Moat Strategy (PRD 3.1)

    Criteria:
    - ROE > 15% (latest quarter)
    - 资产负债率 < 50%
    - 市值 > 100亿 (蓝筹偏好)
    - Financial validation: consistent ROE, low debt
    """

    def __init__(self):
        self.filter_engine = StockFilter()
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute Buffett moat strategy"""
        roe_min = params.get("roe_min", 15.0) if params else 15.0
        debt_max = params.get("debt_max", 50.0) if params else 50.0
        market_cap_min = params.get("market_cap_min", 10_000_000_000) if params else 10_000_000_000

        # Step 1: Screen large caps with positive PE
        conditions = [
            FilterCondition(field="pe", operator=ConditionOperator.GT, value=0),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
        ]
        candidates = await self.filter_engine.apply_filter(conditions)

        # Step 2: Financial quality validation
        results = []
        for stock in candidates[:300]:
            try:
                financials = await self.data_service.fetch_financial_data(
                    stock['stock_code'], years=3
                )
                if not financials or len(financials) < 4:
                    continue

                latest = financials[0]
                roe = latest.get('roe', 0)
                debt_ratio = latest.get('debt_ratio', 100)

                if roe < roe_min:
                    continue
                if debt_ratio > debt_max:
                    continue

                # Check ROE consistency across recent quarters
                roe_values = [f.get('roe', 0) for f in financials[:8] if f.get('roe', 0) > 0]
                if len(roe_values) < 4:
                    continue
                avg_roe = sum(roe_values) / len(roe_values)
                if avg_roe < roe_min * 0.8:
                    continue

                # Score
                score = 40.0
                score += min(roe / 30 * 25, 25)  # ROE contribution
                score += max(0, (50 - debt_ratio) / 50 * 15)  # Lower debt = better
                score += min(len(roe_values) * 2, 10)  # Consistency bonus
                score += min(avg_roe / roe_min * 10, 10)  # Avg ROE bonus

                stock['score'] = round(min(score, 100), 1)
                stock['roe'] = roe
                stock['debt_ratio'] = debt_ratio
                results.append(stock)

            except Exception:
                continue

        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:50]
