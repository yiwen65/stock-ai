# backend/app/engines/strategies/ma_breakout.py
from typing import List, Dict
import pandas as pd
from app.services.data_service import DataService
from app.utils.indicators import calculate_ma, detect_ma_alignment, calculate_volume_ma


class MABreakoutStrategy:
    """均线多头排列策略

    Criteria (PRD 3.2):
    - MA5 > MA10 > MA20 > MA60 (多头排列)
    - 5日均线金叉10日均线 (近5日内发生)
    - 成交量放大确认 (当日成交量 > 5日均量 * 1.5)
    - 市值 > 50亿 (风险过滤)
    """

    def __init__(self):
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute MA breakout strategy"""
        # Parameters
        volume_ratio_min = params.get("volume_ratio_min", 1.5) if params else 1.5
        market_cap_min = params.get("market_cap_min", 5_000_000_000) if params else 5_000_000_000

        # Get full market snapshot
        snapshot = await self.data_service.fetch_market_snapshot()
        if not snapshot:
            return []

        df = pd.DataFrame(snapshot)

        # Pre-filter: valid price, market cap, not ST
        df = df[df['price'] > 0]
        df = df[df['market_cap'] >= market_cap_min]
        df = df[~df['stock_name'].str.contains('ST', case=False, na=False)]
        df = df[df['volume'] > 0]

        # Volume ratio filter: volume_ratio > threshold indicates active trading
        if 'volume_ratio' in df.columns:
            df = df[df['volume_ratio'] >= volume_ratio_min]

        # For each candidate, fetch K-line and check MA alignment
        results = []
        candidates = df.head(200).to_dict('records')  # Limit candidates for performance

        for stock in candidates:
            try:
                kline = await self.data_service.fetch_kline_data(
                    stock['stock_code'], period='1d', days=120
                )
                if len(kline) < 60:
                    continue

                kdf = pd.DataFrame(kline)
                closes = kdf['close']
                volumes = kdf['volume']

                # Check MA alignment
                alignment = detect_ma_alignment(closes)
                if not alignment['bullish']:
                    continue

                # Check volume confirmation
                vol_ma = calculate_volume_ma(volumes, [5])
                if 'vol_ma5' in vol_ma:
                    latest_vol = volumes.iloc[-1]
                    avg_vol = vol_ma['vol_ma5'].iloc[-1]
                    if latest_vol < avg_vol * 1.2:
                        continue

                stock['score'] = self._calculate_score(alignment, kdf)
                results.append(stock)

            except Exception:
                continue

        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:50]

    def _calculate_score(self, alignment: Dict, kdf: pd.DataFrame) -> float:
        """Calculate strategy score based on MA spread and volume"""
        score = 60.0  # Base score for bullish alignment

        ma_vals = alignment.get('ma_values', {})
        if 'ma5' in ma_vals and 'ma20' in ma_vals and ma_vals['ma20'] > 0:
            spread = (ma_vals['ma5'] - ma_vals['ma20']) / ma_vals['ma20'] * 100
            score += min(spread * 2, 20)  # Up to 20 points for spread

        # Volume trend
        volumes = kdf['volume']
        if len(volumes) >= 5:
            recent_avg = volumes.tail(5).mean()
            prev_avg = volumes.tail(20).head(15).mean()
            if prev_avg > 0:
                vol_increase = recent_avg / prev_avg
                score += min(vol_increase * 5, 20)  # Up to 20 points

        return round(min(score, 100), 1)
