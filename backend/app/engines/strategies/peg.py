# backend/app/engines/strategies/peg.py
from typing import List, Dict
from app.engines.stock_filter import StockFilter
from app.services.data_service import DataService
from app.schemas.strategy import FilterCondition, ConditionOperator


class PEGStrategy:
    """PEG Growth Strategy (PRD 3.1)

    Criteria:
    - PEG < 1 (PE / 净利润增长率)
    - 净利润增长率 > 20%
    - ROE > 10%
    - 市值 > 50亿
    """

    def __init__(self):
        self.filter_engine = StockFilter()
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute PEG growth strategy"""
        peg_max = params.get("peg_max", 1.0) if params else 1.0
        growth_min = params.get("growth_min", 20.0) if params else 20.0
        market_cap_min = params.get("market_cap_min", 5_000_000_000) if params else 5_000_000_000

        # Step 1: Screen by PE > 0 and market cap
        conditions = [
            FilterCondition(field="pe", operator=ConditionOperator.GT, value=0),
            FilterCondition(field="pe", operator=ConditionOperator.LT, value=50),
            FilterCondition(field="market_cap", operator=ConditionOperator.GT, value=market_cap_min),
        ]
        candidates = await self.filter_engine.apply_filter(conditions)

        # Step 2: Compute PEG with financial data
        results = []
        for stock in candidates[:300]:
            try:
                financials = await self.data_service.fetch_financial_data(
                    stock['stock_code'], years=2
                )
                if not financials or len(financials) < 2:
                    continue

                latest = financials[0]
                net_profit_growth = latest.get('net_profit_growth', 0)
                roe = latest.get('roe', 0)

                # Must have positive growth above threshold
                if net_profit_growth < growth_min:
                    continue
                if roe < 10:
                    continue

                # Compute PEG
                pe = stock.get('pe', 0)
                if pe <= 0 or net_profit_growth <= 0:
                    continue
                peg = pe / net_profit_growth
                if peg > peg_max:
                    continue

                # Score: lower PEG = better
                score = 50.0
                score += max(0, (peg_max - peg) / peg_max * 25)  # PEG proximity
                score += min(net_profit_growth / 50 * 15, 15)  # Growth bonus
                score += min(roe / 20 * 10, 10)  # ROE bonus

                stock['score'] = round(min(score, 100), 1)
                stock['peg'] = round(peg, 2)
                stock['roe'] = roe
                stock['net_profit_growth'] = net_profit_growth
                results.append(stock)

            except Exception:
                continue

        results.sort(key=lambda x: x.get("peg", 999))
        return results[:50]
