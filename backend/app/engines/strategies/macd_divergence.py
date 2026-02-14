# backend/app/engines/strategies/macd_divergence.py
from typing import List, Dict
import pandas as pd
from app.services.data_service import DataService
from app.utils.indicators import calculate_macd, calculate_rsi


class MACDDivergenceStrategy:
    """MACD 底背离策略

    Criteria (PRD 3.2):
    - 价格创近期新低，但 MACD DIF 不创新低（底背离）
    - RSI < 35 (超卖区域)
    - 成交量萎缩后放量
    - 市值 > 30亿 (风险过滤)
    """

    def __init__(self):
        self.data_service = DataService()

    async def execute(self, params: Dict = None) -> List[Dict]:
        """Execute MACD divergence strategy"""
        rsi_threshold = params.get("rsi_threshold", 35.0) if params else 35.0
        market_cap_min = params.get("market_cap_min", 3_000_000_000) if params else 3_000_000_000
        lookback_days = params.get("lookback_days", 60) if params else 60

        snapshot = await self.data_service.fetch_market_snapshot()
        if not snapshot:
            return []

        df = pd.DataFrame(snapshot)

        # Pre-filter
        df = df[df['price'] > 0]
        df = df[df['market_cap'] >= market_cap_min]
        df = df[~df['stock_name'].str.contains('ST', case=False, na=False)]
        df = df[df['volume'] > 0]

        # Focus on stocks with recent negative returns (potential reversal candidates)
        if 'change_60d' in df.columns:
            df = df[df['change_60d'] < 0]

        results = []
        candidates = df.head(300).to_dict('records')

        for stock in candidates:
            try:
                kline = await self.data_service.fetch_kline_data(
                    stock['stock_code'], period='1d', days=lookback_days + 60
                )
                if len(kline) < lookback_days:
                    continue

                kdf = pd.DataFrame(kline)
                closes = kdf['close']

                # Check RSI oversold
                rsi_data = calculate_rsi(closes, [14])
                rsi14 = rsi_data['rsi14']
                if rsi14.iloc[-1] > rsi_threshold:
                    continue

                # Check MACD divergence
                divergence = self._detect_bottom_divergence(closes, lookback_days)
                if not divergence['detected']:
                    continue

                stock['score'] = divergence['score']
                results.append(stock)

            except Exception:
                continue

        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:50]

    def _detect_bottom_divergence(self, closes: pd.Series, lookback: int) -> Dict:
        """Detect MACD bottom divergence pattern"""
        if len(closes) < lookback:
            return {'detected': False, 'score': 0}

        macd = calculate_macd(closes)
        dif = macd['dif']
        recent_closes = closes.tail(lookback)
        recent_dif = dif.tail(lookback)

        # Find two local minima in price
        price_min_idx = []
        for i in range(2, len(recent_closes) - 2):
            if (recent_closes.iloc[i] <= recent_closes.iloc[i-1] and
                recent_closes.iloc[i] <= recent_closes.iloc[i-2] and
                recent_closes.iloc[i] <= recent_closes.iloc[i+1] and
                recent_closes.iloc[i] <= recent_closes.iloc[i+2]):
                price_min_idx.append(i)

        if len(price_min_idx) < 2:
            return {'detected': False, 'score': 0}

        # Check last two troughs
        idx1 = price_min_idx[-2]
        idx2 = price_min_idx[-1]

        price_lower = recent_closes.iloc[idx2] < recent_closes.iloc[idx1]
        dif_higher = recent_dif.iloc[idx2] > recent_dif.iloc[idx1]

        if price_lower and dif_higher:
            # Score based on divergence strength
            price_drop = (recent_closes.iloc[idx1] - recent_closes.iloc[idx2]) / recent_closes.iloc[idx1]
            dif_rise = recent_dif.iloc[idx2] - recent_dif.iloc[idx1]
            score = 50.0 + min(price_drop * 200, 25) + min(abs(dif_rise) * 10, 25)
            return {'detected': True, 'score': round(min(score, 100), 1)}

        return {'detected': False, 'score': 0}
