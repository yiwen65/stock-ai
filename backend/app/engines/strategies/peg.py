# backend/app/engines/strategies/peg.py
from typing import List, Dict, Optional
from app.engines.stock_filter import StockFilter
from app.engines.strategy_utils import batch_fetch
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

        # Step 2: Compute PEG concurrently
        async def _process(stock: Dict) -> Optional[Dict]:
            financials = await self.data_service.fetch_financial_data(
                stock['stock_code'], years=2
            )
            if not financials or len(financials) < 2:
                return None

            latest = financials[0]
            net_profit_growth = latest.get('net_profit_growth', 0)
            roe = latest.get('roe', 0)

            if net_profit_growth < growth_min:
                return None
            if roe < 10:
                return None

            pe = stock.get('pe', 0)
            if pe <= 0 or net_profit_growth <= 0:
                return None
            peg = pe / net_profit_growth
            if peg > peg_max:
                return None

            score = 50.0
            score += max(0, (peg_max - peg) / peg_max * 25)
            score += min(net_profit_growth / 50 * 15, 15)
            score += min(roe / 20 * 10, 10)

            stock['score'] = round(min(score, 100), 1)
            stock['peg'] = round(peg, 2)
            stock['roe'] = roe
            stock['net_profit_growth'] = net_profit_growth
            return stock

        results = await batch_fetch(candidates[:200], _process)
        results.sort(key=lambda x: x.get("peg", 999))
        return results[:50]
