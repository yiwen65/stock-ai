# backend/app/engines/strategies/shareholder_increase.py
"""股东增持/回购策略 (PRD §3.5.2)

Criteria:
- 近期有大股东增持或公司回购
- 使用北向资金持续流入作为机构增持信号的代理
- 低位增持更有价值（股价处于近60日低位区域）
- 市值 > 20亿, PE > 0, 非ST
"""
from typing import List, Dict
import pandas as pd
from app.services.data_service import DataService
from app.engines.stock_filter import StockFilter


class ShareholderIncreaseStrategy:
    """股东增持/回购策略 — 机构增持信号 + 低位增持 + 基本面过滤"""

    def __init__(self):
        self.data_service = DataService()
        self.filter_engine = StockFilter()

    async def execute(self, params: Dict = None) -> List[Dict]:
        params = params or {}
        market_cap_min = params.get("market_cap_min", 2_000_000_000)
        pe_max = params.get("pe_max", 50.0)

        # 1. Pre-filter
        from app.schemas.strategy import FilterCondition, ConditionOperator
        conditions = [
            FilterCondition(field="market_cap", operator=ConditionOperator.GTE, value=market_cap_min),
            FilterCondition(field="pe", operator=ConditionOperator.GT, value=0),
            FilterCondition(field="pe", operator=ConditionOperator.LTE, value=pe_max),
            FilterCondition(field="price", operator=ConditionOperator.GT, value=0),
        ]
        candidates = await self.filter_engine.apply_filter(conditions)
        if not candidates:
            return []

        # 2. For each candidate, check northbound holding as institutional signal
        results = []
        for stock in candidates[:200]:
            try:
                code = stock['stock_code']

                # Fetch northbound holding data
                holding = await self.data_service.fetch_northbound_stock_holding(code)
                if not holding or not holding.get('change_shares'):
                    continue

                change_shares = holding.get('change_shares', 0)
                if change_shares <= 0:
                    # Skip if no net increase
                    continue

                hold_pct = holding.get('hold_pct', 0)

                # Fetch K-line to check if price is at low position
                kline = await self.data_service.fetch_kline_data(code, period='1d', days=60)
                if not kline or len(kline) < 20:
                    continue

                closes = [float(k['close']) for k in kline if k.get('close')]
                if not closes:
                    continue

                current_price = closes[0]
                high_60d = max(closes)
                low_60d = min(closes)
                price_range = high_60d - low_60d

                # Position in 60-day range (0 = at low, 1 = at high)
                if price_range > 0:
                    position = (current_price - low_60d) / price_range
                else:
                    position = 0.5

                # Prefer low-position increases (position < 0.4)
                low_position = position < 0.4

                # Score
                score = 50.0
                # Northbound holding percentage bonus
                score += min(hold_pct * 2, 15)
                # Increase magnitude (change_shares normalized)
                score += min(change_shares / 1_000_000, 10)
                # Low position bonus
                if low_position:
                    score += 15
                elif position < 0.6:
                    score += 5
                # PE attractiveness
                pe = stock.get('pe', 30)
                if pe and 0 < pe < 15:
                    score += 10
                elif pe and pe < 25:
                    score += 5

                stock['score'] = round(min(score, 100), 1)
                stock['northbound_hold_pct'] = round(hold_pct, 2)
                stock['northbound_change_shares'] = change_shares
                stock['price_position_60d'] = round(position, 2)
                stock['low_position_increase'] = low_position
                results.append(stock)

            except Exception:
                continue

        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:50]
