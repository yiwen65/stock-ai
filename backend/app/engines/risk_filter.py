# backend/app/engines/risk_filter.py
from typing import List, Dict
import pandas as pd

class RiskFilter:
    """Risk filtering engine to remove high-risk stocks

    Filters:
    - ST stocks (Special Treatment)
    - Suspended stocks
    - Low liquidity stocks
    - Small market cap stocks
    """

    def __init__(self):
        self.min_market_cap = 1_000_000_000  # 10亿市值
        self.min_daily_volume = 1_000_000  # 100万日成交量

    async def apply_all_filters(self, stocks: List[Dict]) -> List[Dict]:
        """Apply all risk filters to stock list"""
        if not stocks:
            return []

        df = pd.DataFrame(stocks)

        # Apply each filter
        df = self._filter_st_stocks(df)
        df = self._filter_suspended_stocks(df)
        df = self._filter_low_liquidity(df)
        df = self._filter_small_cap(df)

        return df.to_dict('records')

    def _filter_st_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove ST and *ST stocks (Special Treatment)"""
        if 'stock_name' not in df.columns:
            return df

        # Filter out stocks with ST, *ST, S*ST in name
        mask = ~df['stock_name'].str.contains('ST', case=False, na=False)
        return df[mask]

    def _filter_suspended_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove suspended stocks"""
        # Check if 'status' field exists
        if 'status' in df.columns:
            return df[df['status'] != 'suspended']

        # If no status field, check volume (suspended stocks have 0 volume)
        if 'volume' in df.columns:
            return df[df['volume'] > 0]

        return df

    def _filter_low_liquidity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove stocks with low trading volume"""
        if 'volume' not in df.columns:
            return df

        # Filter out stocks with volume below threshold
        return df[df['volume'] >= self.min_daily_volume]

    def _filter_small_cap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove stocks with market cap below threshold"""
        if 'market_cap' not in df.columns:
            return df

        # Filter out stocks with market cap below threshold
        valid_mask = pd.notna(df['market_cap'])
        df_valid = df[valid_mask]
        return df_valid[df_valid['market_cap'] >= self.min_market_cap]

    def set_min_market_cap(self, min_cap: float):
        """Set minimum market cap threshold"""
        self.min_market_cap = min_cap

    def set_min_volume(self, min_volume: float):
        """Set minimum daily volume threshold"""
        self.min_daily_volume = min_volume
