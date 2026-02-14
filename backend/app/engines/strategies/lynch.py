# backend/app/engines/strategies/lynch.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.services.data_service import DataService
from app.schemas.strategy import FilterCondition, ConditionOperator


class LynchStrategy:
    """Peter Lynch Growth Strategy (PRD 3.1)

    Criteria:
    - PE < 20 (合理估值)
    - 营收增长率 > 15%
    - 净利润增长率 > 15%
    - 资产负债率 < 60%
    - 市值 > 30亿
    """

    def __init__(self):
        self.filter_engine = StockFilter()
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute Lynch growth strategy"""
        pe_max = params.get("pe_max", 20.0) if params else 20.0
        revenue_growth_min = params.get("revenue_growth_min", 15.0) if params else 15.0
        profit_growth_min = params.get("profit_growth_min", 15.0) if params else 15.0
        market_cap_min = params.get("market_cap_min", 3_000_000_000) if params else 3_000_000_000

        # Step 1: Screen by PE and market cap
        conditions = [
            FilterCondition(field="pe", operator=ConditionOperator.GT, value=0),
            FilterCondition(field="pe", operator=ConditionOperator.LT, value=pe_max),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
        ]
        candidates = await self.filter_engine.apply_filter(conditions)

        # Step 2: Validate growth with financial data
        results = []
        for stock in candidates[:300]:
            try:
                financials = await self.data_service.fetch_financial_data(
                    stock['stock_code'], years=2
                )
                if not financials or len(financials) < 2:
                    continue

                latest = financials[0]
                revenue_growth = latest.get('revenue_growth', 0)
                net_profit_growth = latest.get('net_profit_growth', 0)
                debt_ratio = latest.get('debt_ratio', 100)
                roe = latest.get('roe', 0)

                if revenue_growth < revenue_growth_min:
                    continue
                if net_profit_growth < profit_growth_min:
                    continue
                if debt_ratio > 60:
                    continue

                # Score: balance of growth + value
                pe = stock.get('pe', pe_max)
                score = 40.0
                score += min(net_profit_growth / 50 * 20, 20)  # Growth
                score += min(revenue_growth / 50 * 15, 15)  # Revenue growth
                score += max(0, (pe_max - pe) / pe_max * 15)  # Value discount
                score += min(roe / 20 * 10, 10)  # ROE bonus

                stock['score'] = round(min(score, 100), 1)
                stock['roe'] = roe
                stock['revenue_growth'] = revenue_growth
                stock['net_profit_growth'] = net_profit_growth
                stock['debt_ratio'] = debt_ratio
                results.append(stock)

            except Exception:
                continue

        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:50]
