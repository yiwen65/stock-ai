# backend/app/engines/risk_filter.py
from typing import List, Dict, Optional, Set
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class RiskFilter:
    """Risk filtering engine to remove high-risk stocks

    Filters:
    - ST stocks (Special Treatment)
    - Suspended stocks
    - Low liquidity stocks
    - Small market cap stocks
    - Daily limit stocks (涨跌停)
    - Invalid price stocks
    - Industry include/exclude
    """

    def __init__(self):
        self.min_market_cap = 1_000_000_000  # 10亿市值
        self.min_daily_volume = 1_000_000  # 100万日成交量
        self._industry_include: Optional[Set[str]] = None
        self._industry_exclude: Optional[Set[str]] = None
        self._industry_stock_cache: Optional[Dict[str, str]] = None

    def set_industry_filter(
        self,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ):
        """Set industry include/exclude filter.
        Args:
            include: Only keep stocks in these industries (行业名称)
            exclude: Remove stocks in these industries
        """
        self._industry_include = set(include) if include else None
        self._industry_exclude = set(exclude) if exclude else None

    async def _load_industry_map(self) -> Dict[str, str]:
        """Load stock_code → industry_name mapping (cached)."""
        if self._industry_stock_cache is not None:
            return self._industry_stock_cache
        try:
            import akshare as ak
            df = ak.stock_board_industry_cons_em(symbol="全部")
            if not df.empty and "代码" in df.columns and "板块名称" in df.columns:
                self._industry_stock_cache = dict(zip(df["代码"].astype(str), df["板块名称"].astype(str)))
            else:
                self._industry_stock_cache = {}
        except Exception as e:
            logger.warning(f"Failed to load industry map: {e}")
            self._industry_stock_cache = {}
        return self._industry_stock_cache

    async def apply_all_filters(self, stocks: List[Dict]) -> List[Dict]:
        """Apply all risk filters to stock list"""
        if not stocks:
            return []

        df = pd.DataFrame(stocks)

        # Apply each filter
        df = self._filter_st_stocks(df)
        df = self._filter_suspended_stocks(df)
        df = self._filter_invalid_price(df)
        df = self._filter_daily_limit(df)
        df = self._filter_low_liquidity(df)
        df = self._filter_small_cap(df)

        # Apply industry filter if configured
        if self._industry_include or self._industry_exclude:
            df = await self._filter_by_industry(df)

        return df.to_dict('records')

    async def _filter_by_industry(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter stocks by industry include/exclude lists."""
        if df.empty:
            return df
        industry_map = await self._load_industry_map()
        if not industry_map:
            return df

        codes = df['stock_code'].astype(str)
        industries = codes.map(lambda c: industry_map.get(c, ''))

        if self._industry_include:
            mask = industries.isin(self._industry_include)
            df = df[mask]
        if self._industry_exclude:
            mask = ~industries.isin(self._industry_exclude)
            df = df[mask]
        return df

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

    def _filter_invalid_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove stocks with invalid or zero price"""
        if 'price' not in df.columns:
            return df
        valid = pd.notna(df['price'])
        return df[valid & (df['price'] > 0)]

    def _filter_daily_limit(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove stocks that hit daily up/down limit (涨跌停)"""
        if 'pct_change' not in df.columns:
            return df
        valid = pd.notna(df['pct_change'])
        df_valid = df[valid]
        # A-share daily limit is typically 10% (20% for ChiNext/STAR)
        # Filter out stocks at or very near the limit
        return df_valid[(df_valid['pct_change'] > -9.8) & (df_valid['pct_change'] < 9.8)]

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
