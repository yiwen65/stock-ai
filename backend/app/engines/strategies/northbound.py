# backend/app/engines/strategies/northbound.py
from typing import List, Dict, Optional
import pandas as pd
from app.engines.strategy_utils import batch_fetch
from app.services.data_service import DataService


class NorthboundStrategy:
    """北向资金持续流入策略

    Criteria (PRD 3.3):
    - 北向资金连续N日净流入
    - PE < 30 (估值合理)
    - 市值 > 100亿 (蓝筹偏好)

    Note: This strategy uses per-stock capital flow as proxy
    since per-stock northbound data requires Tushare Pro.
    Falls back to main capital flow analysis.
    """

    def __init__(self):
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute northbound capital strategy"""
        pe_max = params.get("pe_max", 30.0) if params else 30.0
        market_cap_min = params.get("market_cap_min", 10_000_000_000) if params else 10_000_000_000

        snapshot = await self.data_service.fetch_market_snapshot()
        if not snapshot:
            return []

        df = pd.DataFrame(snapshot)

        # Pre-filter: large caps with reasonable PE
        df = df[df['price'] > 0]
        df = df[df['market_cap'] >= market_cap_min]
        df = df[~df['stock_name'].str.contains('ST', case=False, na=False)]
        df = df[df['volume'] > 0]
        df = df[pd.notna(df['pe'])]
        df = df[(df['pe'] > 0) & (df['pe'] < pe_max)]

        # Sort by market cap descending - focus on large caps
        df = df.sort_values('market_cap', ascending=False)

        candidates = df.head(200).to_dict('records')

        # Fetch capital flow concurrently
        async def _process(stock: Dict) -> Optional[Dict]:
            flow = await self.data_service.fetch_capital_flow(stock['stock_code'])
            if not flow:
                return None

            main_5d = flow.get('main_net_inflow_5d', 0)
            main_10d = flow.get('main_net_inflow_10d', 0)
            main_today = flow.get('main_net_inflow', 0)

            if main_today <= 0 or main_5d <= 0:
                return None

            score = 50.0
            if main_5d > 0:
                score += 15
            if main_10d > 0:
                score += 10
            if stock['market_cap'] > 0:
                inflow_pct = main_5d / stock['market_cap'] * 100
                score += min(inflow_pct * 50, 25)

            stock['score'] = round(min(score, 100), 1)
            stock['main_net_inflow_5d'] = main_5d
            stock['main_net_inflow_10d'] = main_10d
            return stock

        results = await batch_fetch(candidates, _process)
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:50]
