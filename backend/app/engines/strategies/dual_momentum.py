# backend/app/engines/strategies/dual_momentum.py
"""双动量策略 (PRD §3.3.2)

Criteria:
- 绝对动量：60日涨幅 > 10%
- 相对动量：跑赢沪深300同期涨幅
- 回撤控制：近20日最大回撤 < 15%
- 成交量确认：近5日均量 > 近20日均量
- 市值 > 30亿, 非ST, 非停牌
"""
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from app.engines.strategy_utils import batch_fetch
from app.services.data_service import DataService
from app.engines.stock_filter import StockFilter


class DualMomentumStrategy:
    """双动量策略 — 绝对动量 + 相对动量 + 回撤控制"""

    def __init__(self):
        self.data_service = DataService()
        self.filter_engine = StockFilter()

    async def execute(self, params: Dict = None) -> List[Dict]:
        params = params or {}
        abs_momentum_min = params.get("abs_momentum_min", 10.0)
        max_drawdown = params.get("max_drawdown", 15.0)
        market_cap_min = params.get("market_cap_min", 3_000_000_000)

        # 1. Get benchmark (沪深300) 60-day return
        benchmark_return = await self._get_benchmark_return()

        # 2. Pre-filter from market snapshot
        from app.schemas.strategy import FilterCondition, ConditionOperator
        conditions = [
            FilterCondition(field="market_cap", operator=ConditionOperator.GTE, value=market_cap_min),
            FilterCondition(field="price", operator=ConditionOperator.GT, value=0),
        ]
        candidates = await self.filter_engine.apply_filter(conditions)
        if not candidates:
            return []

        # 3. Filter by 60-day return from snapshot
        df = pd.DataFrame(candidates)
        if 'change_60d' in df.columns:
            df = df[pd.notna(df['change_60d'])]
            df = df[df['change_60d'] >= abs_momentum_min]
        else:
            return []

        stock_list = df.head(200).to_dict('records')

        # 4. Fetch K-line and validate concurrently
        async def _process(stock: Dict) -> Optional[Dict]:
            kline = await self.data_service.fetch_kline_data(
                stock['stock_code'], period='1d', days=80
            )
            if not kline or len(kline) < 20:
                return None

            closes = [float(k['close']) for k in kline if k.get('close')]
            if len(closes) < 20:
                return None

            ret_60d = stock.get('change_60d', 0)
            if ret_60d < abs_momentum_min:
                return None

            if benchmark_return is not None and ret_60d <= benchmark_return:
                return None

            recent_closes = closes[:20]
            peak = recent_closes[0]
            dd = 0
            for c in recent_closes:
                if c > peak:
                    peak = c
                dd = max(dd, (peak - c) / peak * 100)
            if dd > max_drawdown:
                return None

            volumes = [float(k.get('volume', 0)) for k in kline[:20]]
            if len(volumes) >= 20:
                vol_5 = np.mean(volumes[:5])
                vol_20 = np.mean(volumes[:20])
                vol_confirm = vol_5 > vol_20
            else:
                vol_confirm = True

            score = 50.0
            score += min(ret_60d * 0.5, 25)
            if benchmark_return is not None:
                excess = ret_60d - benchmark_return
                score += min(excess * 0.3, 10)
            score += max(0, (max_drawdown - dd)) * 0.5
            if vol_confirm:
                score += 5

            stock['score'] = round(min(score, 100), 1)
            stock['return_60d'] = round(ret_60d, 2)
            stock['max_drawdown_20d'] = round(dd, 2)
            return stock

        results = await batch_fetch(stock_list, _process)
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:50]

    async def _get_benchmark_return(self) -> float | None:
        """Get CSI 300 (沪深300) 60-day return."""
        try:
            import akshare as ak
            df = ak.stock_zh_index_daily_em(symbol="sh000300")
            if df.empty or len(df) < 60:
                return None
            closes = df['close'].astype(float).tolist()
            return (closes[-1] / closes[-60] - 1) * 100
        except Exception:
            return None
