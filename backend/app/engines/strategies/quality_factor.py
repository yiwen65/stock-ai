# backend/app/engines/strategies/quality_factor.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.services.data_service import DataService
from app.schemas.strategy import FilterCondition, ConditionOperator


class QualityFactorStrategy:
    """Quality Factor Strategy

    Criteria:
    - High ROE (>12%)
    - Low debt ratio (<50%)
    - Stable revenue growth
    - Reasonable valuation (PE < 40)
    - Market cap > 5B
    """

    def __init__(self):
        self.filter_engine = StockFilter()
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute quality factor strategy"""
        roe_min = params.get("roe_min", 12.0) if params else 12.0
        pe_max = params.get("pe_max", 40.0) if params else 40.0
        market_cap_min = params.get("market_cap_min", 5_000_000_000) if params else 5_000_000_000

        # Screen by PE + market cap
        conditions = [
            FilterCondition(field="pe", operator=ConditionOperator.GT, value=0),
            FilterCondition(field="pe", operator=ConditionOperator.LT, value=pe_max),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
        ]
        candidates = await self.filter_engine.apply_filter(conditions)

        # Validate financial quality
        results = []
        for stock in candidates[:200]:
            try:
                financials = await self.data_service.fetch_financial_data(
                    stock["stock_code"], years=3
                )
                if not financials or len(financials) < 4:
                    continue

                latest = financials[0]
                roe = latest.get("roe", 0)
                debt_ratio = latest.get("debt_ratio", 100)
                gross_margin = latest.get("gross_margin", 0)
                net_margin = latest.get("net_margin", 0)
                revenue_growth = latest.get("revenue_growth", 0)

                if roe < roe_min:
                    continue
                if debt_ratio > 50:
                    continue

                # ROE stability: check std across quarters
                roe_values = [f.get("roe", 0) for f in financials[:8]]
                roe_values = [r for r in roe_values if r > 0]
                if len(roe_values) < 3:
                    continue
                roe_avg = sum(roe_values) / len(roe_values)
                roe_std = (sum((r - roe_avg) ** 2 for r in roe_values) / len(roe_values)) ** 0.5

                # Score: high ROE + low debt + high margin + stable ROE + growth
                score = 0
                score += min(roe / 25 * 30, 30)  # ROE contribution
                score += max(0, (50 - debt_ratio) / 50 * 20)  # Low debt
                score += min(gross_margin / 50 * 15, 15)  # Gross margin
                score += min(net_margin / 20 * 10, 10)  # Net margin
                score += max(0, min(revenue_growth / 30 * 15, 15))  # Growth
                score -= min(roe_std * 2, 10)  # Penalize ROE instability
                score = max(0, min(100, score))

                stock["score"] = round(score, 1)
                stock["roe"] = roe
                stock["risk_level"] = "low" if debt_ratio < 30 and roe > 15 else "medium"
                results.append(stock)

            except Exception:
                continue

        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:50]
