# backend/app/engines/strategies/earnings_surprise.py
from typing import List, Dict
import pandas as pd
from app.services.data_service import DataService


class EarningsSurpriseStrategy:
    """业绩预增/扭亏事件驱动策略

    Criteria (PRD 3.3):
    - 近期发布业绩预增/扭亏公告
    - 净利润增长率 > 30%
    - PE < 行业平均 or PE < 30
    - 市值 > 30亿 (风险过滤)

    Note: Since AKShare earnings forecast data may vary,
    this strategy uses financial growth metrics as a proxy.
    """

    def __init__(self):
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute earnings surprise strategy"""
        min_profit_growth = params.get("min_profit_growth", 30.0) if params else 30.0
        pe_max = params.get("pe_max", 30.0) if params else 30.0
        market_cap_min = params.get("market_cap_min", 3_000_000_000) if params else 3_000_000_000

        snapshot = await self.data_service.fetch_market_snapshot()
        if not snapshot:
            return []

        df = pd.DataFrame(snapshot)

        # Pre-filter
        df = df[df['price'] > 0]
        df = df[df['market_cap'] >= market_cap_min]
        df = df[~df['stock_name'].str.contains('ST', case=False, na=False)]
        df = df[df['volume'] > 0]

        # PE filter
        df = df[pd.notna(df['pe'])]
        df = df[(df['pe'] > 0) & (df['pe'] < pe_max)]

        results = []
        candidates = df.head(500).to_dict('records')

        for stock in candidates:
            try:
                financials = await self.data_service.fetch_financial_data(
                    stock['stock_code'], years=2
                )
                if not financials or len(financials) < 2:
                    continue

                latest = financials[0]
                net_profit_growth = latest.get('net_profit_growth', 0)

                # Check earnings growth
                if net_profit_growth < min_profit_growth:
                    continue

                # Check revenue growth as confirmation
                revenue_growth = latest.get('revenue_growth', 0)

                # Score: weighted by growth magnitude
                score = 50.0
                score += min(net_profit_growth * 0.5, 30)  # Up to 30 pts for profit growth
                score += min(max(revenue_growth, 0) * 0.3, 10)  # Up to 10 pts for revenue
                if stock.get('pe') and stock['pe'] < 20:
                    score += 10  # Low PE bonus

                stock['score'] = round(min(score, 100), 1)
                stock['net_profit_growth'] = net_profit_growth
                stock['revenue_growth'] = revenue_growth
                results.append(stock)

            except Exception:
                continue

        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:50]
