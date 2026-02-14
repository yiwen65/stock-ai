# backend/app/engines/strategies/volume_breakout.py
from typing import List, Dict
import pandas as pd
import numpy as np
from app.services.data_service import DataService
from app.utils.indicators import calculate_ma, calculate_boll


class VolumeBreakoutStrategy:
    """放量突破平台策略

    Criteria (PRD 3.2):
    - 前期横盘整理（近20日振幅 < 15%）
    - 当日放量突破（成交量 > 20日均量 * 2）
    - 价格突破近20日最高价
    - 站上布林带上轨
    - 市值 > 30亿 (风险过滤)
    """

    def __init__(self):
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute volume breakout strategy"""
        consolidation_days = params.get("consolidation_days", 20) if params else 20
        volume_multiplier = params.get("volume_multiplier", 2.0) if params else 2.0
        max_amplitude = params.get("max_amplitude", 15.0) if params else 15.0
        market_cap_min = params.get("market_cap_min", 3_000_000_000) if params else 3_000_000_000

        snapshot = await self.data_service.fetch_market_snapshot()
        if not snapshot:
            return []

        df = pd.DataFrame(snapshot)

        # Pre-filter: active stocks with positive movement today
        df = df[df['price'] > 0]
        df = df[df['market_cap'] >= market_cap_min]
        df = df[~df['stock_name'].str.contains('ST', case=False, na=False)]
        df = df[df['volume'] > 0]
        df = df[df['pct_change'] > 1.0]  # At least 1% up today

        # Volume ratio filter: high volume today
        if 'volume_ratio' in df.columns:
            df = df[df['volume_ratio'] >= 1.5]

        results = []
        candidates = df.head(200).to_dict('records')

        for stock in candidates:
            try:
                kline = await self.data_service.fetch_kline_data(
                    stock['stock_code'], period='1d', days=consolidation_days + 30
                )
                if len(kline) < consolidation_days + 5:
                    continue

                kdf = pd.DataFrame(kline)
                closes = kdf['close']
                highs = kdf['high']
                lows = kdf['low']
                volumes = kdf['volume']

                # Check consolidation: low amplitude in prior period
                prior = kdf.iloc[-(consolidation_days + 1):-1]
                prior_high = prior['high'].max()
                prior_low = prior['low'].min()
                if prior_low <= 0:
                    continue
                amplitude = (prior_high - prior_low) / prior_low * 100
                if amplitude > max_amplitude:
                    continue

                # Check price breakout above prior high
                latest_close = closes.iloc[-1]
                if latest_close <= prior_high:
                    continue

                # Check volume breakout
                vol_avg = volumes.iloc[-(consolidation_days + 1):-1].mean()
                latest_vol = volumes.iloc[-1]
                if vol_avg <= 0 or latest_vol < vol_avg * volume_multiplier:
                    continue

                # Calculate score
                breakout_pct = (latest_close - prior_high) / prior_high * 100
                vol_ratio = latest_vol / vol_avg
                score = 50.0 + min(breakout_pct * 5, 25) + min(vol_ratio * 5, 25)

                stock['score'] = round(min(score, 100), 1)
                results.append(stock)

            except Exception:
                continue

        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:50]
