# backend/app/services/data_service.py
import asyncio
import json
import time
import akshare as ak
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory L2 cache (for data that rarely changes / fallback)
# ---------------------------------------------------------------------------
_memory_cache: Dict[str, dict] = {}   # key → {"data": ..., "ts": float}

SNAPSHOT_CACHE_KEY = "market:snapshot"
SNAPSHOT_TTL = 30           # Redis TTL seconds (real-time, refresh often)
SNAPSHOT_MEMORY_TTL = 120   # L2 memory fallback TTL
SECTOR_TTL = 300            # sectors change slower
STOCK_LIST_TTL = 3600       # stock list changes daily at most
KLINE_TTL = 600
FINANCIAL_TTL = 3600
CAPITAL_FLOW_TTL = 300


def _safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        if value is False or value is None:
            return default
        if pd.isna(value) or value == '' or value == '-':
            return default
        s = str(value).strip().rstrip('%')
        if s == '' or s == '-' or s.lower() == 'false':
            return default
        return float(s)
    except (ValueError, TypeError):
        return default


def _parse_cn_amount(value, default: float = 0.0) -> float:
    """Parse Chinese amount strings like '5.89亿', '-5789.53万' to float (yuan)"""
    try:
        if value is False or value is None:
            return default
        if pd.isna(value) or value == '' or value == '-':
            return default
        s = str(value).strip()
        if s.endswith('亿'):
            return float(s[:-1]) * 1e8
        elif s.endswith('万'):
            return float(s[:-1]) * 1e4
        return float(s)
    except (ValueError, TypeError):
        return default


def _safe_int(value, default: int = 0) -> int:
    """Safely convert value to int"""
    try:
        if pd.isna(value) or value == '' or value == '-':
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def _normalize_stock_code(value) -> str:
    """Normalize stock code to 6-digit string.

    Handles cases like int/float (e.g. 600519 / 600519.0) and prefixed strings.
    """
    if value is None:
        return ""

    s = str(value).strip()
    if not s:
        return ""

    if s.endswith('.0'):
        s = s[:-2]

    digits = ''.join(ch for ch in s if ch.isdigit())
    if not digits:
        return ""
    if len(digits) >= 6:
        return digits[-6:]
    return digits.zfill(6)


def _mem_get(key: str, ttl: int = 120):
    """Get from in-memory L2 cache"""
    entry = _memory_cache.get(key)
    if entry and (time.time() - entry["ts"]) < ttl:
        return entry["data"]
    return None


def _mem_set(key: str, data):
    """Set to in-memory L2 cache"""
    _memory_cache[key] = {"data": data, "ts": time.time()}


class DataService:
    """Data service with Redis L1 + memory L2 caching and AKShare fallback."""

    def __init__(self):
        self._redis = None

    @property
    def redis(self):
        """Lazy-init Redis client (tolerate unavailable Redis)."""
        if self._redis is None:
            try:
                from app.core.cache import redis_client
                redis_client.ping()
                self._redis = redis_client
            except Exception:
                self._redis = False  # sentinel: Redis unavailable
        return self._redis if self._redis is not False else None

    # ------------------------------------------------------------------
    # Redis helpers with fallback
    # ------------------------------------------------------------------
    def _cache_get(self, key: str):
        """Try Redis → memory fallback."""
        try:
            if self.redis:
                val = self.redis.get(key)
                if val:
                    return json.loads(val)
        except Exception as e:
            logger.debug(f"Redis get miss for {key}: {e}")
        return None

    def _cache_set(self, key: str, data, ttl: int = 60):
        """Write to Redis + memory."""
        _mem_set(key, data)
        try:
            if self.redis:
                self.redis.setex(key, ttl, json.dumps(data, default=str))
        except Exception as e:
            logger.debug(f"Redis set fail for {key}: {e}")

    # ------------------------------------------------------------------
    # Row conversion
    # ------------------------------------------------------------------
    def _row_to_full_quote(self, row) -> Dict:
        """Convert a single row from stock_zh_a_spot_em to a full quote dict"""
        return {
            "stock_code": _normalize_stock_code(row["代码"]),
            "stock_name": str(row["名称"]),
            "price": _safe_float(row["最新价"]),
            "change": _safe_float(row["涨跌额"]),
            "pct_change": _safe_float(row["涨跌幅"]),
            "volume": _safe_int(row["成交量"]),
            "amount": _safe_float(row["成交额"]),
            "amplitude": _safe_float(row["振幅"]),
            "high": _safe_float(row["最高"]),
            "low": _safe_float(row["最低"]),
            "open": _safe_float(row["今开"]),
            "pre_close": _safe_float(row["昨收"]),
            "volume_ratio": _safe_float(row["量比"]),
            "turnover_rate": _safe_float(row["换手率"]),
            "pe": _safe_float(row["市盈率-动态"], default=None),
            "pb": _safe_float(row["市净率"], default=None),
            "market_cap": _safe_float(row["总市值"]),
            "circulating_market_cap": _safe_float(row["流通市值"]),
            "change_speed": _safe_float(row["涨速"]),
            "change_5min": _safe_float(row["5分钟涨跌"]),
            "change_60d": _safe_float(row["60日涨跌幅"]),
            "change_ytd": _safe_float(row["年初至今涨跌幅"]),
            "timestamp": datetime.now().isoformat()
        }

    # ------------------------------------------------------------------
    # Market snapshot (with Redis L1 + memory L2 caching)
    # ------------------------------------------------------------------
    async def fetch_market_snapshot(self) -> List[Dict]:
        """Fetch full market snapshot with all fields.

        Cache chain: Redis (30s) → Memory (120s) → AKShare API.
        """
        # L1: Redis
        cached = self._cache_get(SNAPSHOT_CACHE_KEY)
        if cached:
            return cached

        # L2: memory
        mem = _mem_get(SNAPSHOT_CACHE_KEY, SNAPSHOT_MEMORY_TTL)
        if mem:
            return mem

        # L3: AKShare (run in thread to avoid blocking event loop)
        try:
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            results = [self._row_to_full_quote(row) for _, row in df.iterrows()]
            self._cache_set(SNAPSHOT_CACHE_KEY, results, SNAPSHOT_TTL)
            logger.info(f"Market snapshot fetched: {len(results)} stocks")
            return results
        except Exception as e:
            logger.error(f"Error fetching market snapshot: {e}")
            # Final fallback: stale memory cache (ignore TTL)
            stale = _memory_cache.get(SNAPSHOT_CACHE_KEY)
            if stale:
                logger.warning("Using stale memory cache for market snapshot")
                return stale["data"]
            return []

    async def fetch_stock_list(self) -> List[Dict]:
        """Fetch A-share stock list from AKShare (cached 1h)"""
        cache_key = "data:stock_list"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        mem = _mem_get(cache_key, STOCK_LIST_TTL)
        if mem:
            return mem

        # Primary: SH + SZ exchange APIs (fast ~10s, avoids BSE proxy hang)
        try:
            df_sh, df_sz = await asyncio.gather(
                asyncio.to_thread(ak.stock_info_sh_name_code),
                asyncio.to_thread(ak.stock_info_sz_name_code),
            )
            stocks = []
            for _, row in df_sh.iterrows():
                stocks.append({"stock_code": _normalize_stock_code(row["证券代码"]), "stock_name": str(row["证券简称"])})
            for _, row in df_sz.iterrows():
                stocks.append({"stock_code": _normalize_stock_code(row["证券代码"]), "stock_name": str(row["证券简称"])})
            if stocks:
                self._cache_set(cache_key, stocks, STOCK_LIST_TTL)
                logger.info(f"Stock list fetched via SH+SZ: {len(stocks)} stocks")
                return stocks
        except Exception as e:
            logger.warning(f"SH+SZ stock list failed: {e}, trying fallback via spot_em")

        # Fallback: East Money spot API (slower ~120s but comprehensive)
        try:
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            stocks = [
                {"stock_code": _normalize_stock_code(row["代码"]), "stock_name": str(row["名称"])}
                for _, row in df.iterrows()
            ]
            if stocks:
                self._cache_set(cache_key, stocks, STOCK_LIST_TTL)
                logger.info(f"Stock list fallback via spot_em: {len(stocks)} stocks")
                return stocks
        except Exception as e2:
            logger.error(f"Stock list fallback also failed: {e2}")

        stale = _memory_cache.get(cache_key)
        return stale["data"] if stale else []

    async def get_all_stock_codes(self) -> List[str]:
        """Get all stock codes"""
        stocks = await self.fetch_stock_list()
        return [s["stock_code"] for s in stocks]

    # ------------------------------------------------------------------
    # Real-time quotes (use cached snapshot when possible)
    # ------------------------------------------------------------------
    def get_cached_snapshot(self) -> Optional[List[Dict]]:
        """Return snapshot ONLY if already cached (no API call). For fast lookups."""
        cached = self._cache_get(SNAPSHOT_CACHE_KEY)
        if cached:
            return cached
        return _mem_get(SNAPSHOT_CACHE_KEY, SNAPSHOT_MEMORY_TTL)

    async def fetch_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """Fetch real-time quote for a stock — uses cached snapshot."""
        target_code = _normalize_stock_code(stock_code)
        snapshot = await self.fetch_market_snapshot()
        for s in snapshot:
            if _normalize_stock_code(s.get("stock_code")) == target_code:
                return s
        return None

    async def fetch_realtime_quotes_batch(self, stock_codes: List[str]) -> List[Dict]:
        """Fetch real-time quotes for multiple stocks — uses cached snapshot."""
        code_set = {_normalize_stock_code(c) for c in stock_codes}
        snapshot = await self.fetch_market_snapshot()
        return [s for s in snapshot if _normalize_stock_code(s.get("stock_code")) in code_set]

    # ------------------------------------------------------------------
    # Capital flow
    # ------------------------------------------------------------------
    async def fetch_capital_flow(self, stock_code: str) -> Optional[Dict]:
        """Fetch capital flow data for a stock (主力资金流向)"""
        cache_key = f"data:capital_flow:{stock_code}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        try:
            market = "sh" if stock_code.startswith("6") else "sz"
            df = await asyncio.to_thread(ak.stock_individual_fund_flow, stock=stock_code, market=market)
            if df.empty:
                return None

            recent = df.tail(20)
            today = recent.iloc[-1] if len(recent) > 0 else None
            if today is None:
                return None

            def _col_sum(col: str, n: int) -> float:
                if col not in recent.columns:
                    return 0.0
                return _safe_float(recent.tail(n)[col].sum())

            result = {
                "stock_code": stock_code,
                "date": str(today.get("日期", "")),
                # Today
                "main_net_inflow": _safe_float(today.get("主力净流入-净额", 0)),
                "main_net_inflow_pct": _safe_float(today.get("主力净流入-净占比", 0)),
                "super_large_net_inflow": _safe_float(today.get("超大单净流入-净额", 0)),
                "large_net_inflow": _safe_float(today.get("大单净流入-净额", 0)),
                "medium_net_inflow": _safe_float(today.get("中单净流入-净额", 0)),
                "small_net_inflow": _safe_float(today.get("小单净流入-净额", 0)),
                # 5-day aggregates
                "main_net_inflow_5d": _col_sum("主力净流入-净额", 5),
                "super_large_net_inflow_5d": _col_sum("超大单净流入-净额", 5),
                "large_net_inflow_5d": _col_sum("大单净流入-净额", 5),
                # 10-day aggregates
                "main_net_inflow_10d": _col_sum("主力净流入-净额", 10),
                "super_large_net_inflow_10d": _col_sum("超大单净流入-净额", 10),
                "large_net_inflow_10d": _col_sum("大单净流入-净额", 10),
                # 20-day aggregate
                "main_net_inflow_20d": _col_sum("主力净流入-净额", 20),
            }
            self._cache_set(cache_key, result, CAPITAL_FLOW_TTL)
            return result
        except Exception as e:
            logger.error(f"Error fetching capital flow for {stock_code}: {e}")
            return None

    # ------------------------------------------------------------------
    # Valuation history (PE/PB percentile)
    # ------------------------------------------------------------------
    async def fetch_valuation_history(self, stock_code: str) -> Optional[Dict]:
        """Fetch historical PE_TTM / PB data for percentile calculation (cached 1h)"""
        cache_key = f"data:valuation_hist:{stock_code}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        result: Dict = {}

        def _calc_percentile(symbol: str, indicator: str) -> Optional[Dict]:
            try:
                df = ak.stock_zh_valuation_baidu(symbol=symbol, indicator=indicator, period="近一年")
                if df is None or df.empty:
                    return None
                series = pd.to_numeric(df['value'], errors='coerce').dropna()
                series = series[series > 0]
                if len(series) < 30:
                    return None
                current = float(series.iloc[-1])
                pct = float((series < current).sum() / len(series) * 100)
                return {
                    'percentile': round(pct, 1),
                    'min': round(float(series.min()), 2),
                    'max': round(float(series.max()), 2),
                    'median': round(float(series.median()), 2),
                    'current': round(current, 2),
                }
            except Exception:
                return None

        try:
            pe_data, pb_data = await asyncio.gather(
                asyncio.to_thread(_calc_percentile, stock_code, "市盈率(TTM)"),
                asyncio.to_thread(_calc_percentile, stock_code, "市净率"),
            )
            if pe_data:
                result['pe_percentile'] = pe_data['percentile']
                result['pe_values'] = {k: v for k, v in pe_data.items() if k != 'percentile'}
            if pb_data:
                result['pb_percentile'] = pb_data['percentile']
                result['pb_values'] = {k: v for k, v in pb_data.items() if k != 'percentile'}

            if result:
                self._cache_set(cache_key, result, FINANCIAL_TTL)
                return result
            return None
        except Exception as e:
            logger.warning(f"Valuation history fetch failed for {stock_code}: {e}")
            return None

    # ------------------------------------------------------------------
    # Sector list
    # ------------------------------------------------------------------
    async def fetch_sector_list(self) -> List[Dict]:
        """Fetch industry sector list with performance data (cached 5min)"""
        cache_key = "data:sector_list"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        try:
            df = await asyncio.to_thread(ak.stock_board_industry_name_em)
            sectors = []
            for _, row in df.iterrows():
                sectors.append({
                    "sector_name": str(row.get("板块名称", "")),
                    "sector_code": str(row.get("板块代码", "")),
                    "pct_change": _safe_float(row.get("涨跌幅", 0)),
                    "turnover": _safe_float(row.get("总成交额", 0)),
                    "leader_stock": str(row.get("领涨股票", "")),
                    "leader_pct_change": _safe_float(row.get("领涨股票-涨跌幅", 0)),
                })
            self._cache_set(cache_key, sectors, SECTOR_TTL)
            return sectors
        except Exception as e:
            logger.error(f"Error fetching sector list: {e}")
            stale = _memory_cache.get(cache_key)
            return stale["data"] if stale else []

    # ------------------------------------------------------------------
    # K-line data
    # ------------------------------------------------------------------
    async def fetch_kline_data(
        self,
        stock_code: str,
        period: str = '1d',
        days: int = 500
    ) -> List[Dict]:
        """Fetch K-line data for a stock (cached 10min)"""
        cache_key = f"data:kline:{stock_code}:{period}:{days}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            period_map = {'1d': 'daily', '1w': 'weekly', '1M': 'monthly'}
            ak_period = period_map.get(period, 'daily')

            df = await asyncio.to_thread(
                ak.stock_zh_a_hist,
                symbol=stock_code,
                period=ak_period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

            kline_data = []
            for _, row in df.iterrows():
                kline_data.append({
                    "date": str(row["日期"]),
                    "open": float(row["开盘"]),
                    "high": float(row["最高"]),
                    "low": float(row["最低"]),
                    "close": float(row["收盘"]),
                    "volume": int(row["成交量"]),
                    "amount": float(row["成交额"])
                })
            self._cache_set(cache_key, kline_data, KLINE_TTL)
            return kline_data
        except Exception as e:
            logger.error(f"Error fetching kline data for {stock_code}: {e}")
            return []

    # ------------------------------------------------------------------
    # Market capital flow
    # ------------------------------------------------------------------
    async def fetch_market_capital_flow(self) -> List[Dict]:
        """Fetch market-level capital flow by sector (cached 5min)"""
        cache_key = "data:market_capital_flow"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        try:
            df = await asyncio.to_thread(ak.stock_sector_fund_flow_rank, indicator="今日", sector_type="行业资金流")
            if df.empty:
                return []

            results = []
            for _, row in df.head(30).iterrows():
                results.append({
                    "sector_name": str(row.get("名称", "")),
                    "main_net_inflow": _safe_float(row.get("主力净流入-净额", 0)),
                    "main_net_inflow_pct": _safe_float(row.get("主力净流入-净占比", 0)),
                    "super_large_net": _safe_float(row.get("超大单净流入-净额", 0)),
                    "large_net": _safe_float(row.get("大单净流入-净额", 0)),
                    "medium_net": _safe_float(row.get("中单净流入-净额", 0)),
                    "small_net": _safe_float(row.get("小单净流入-净额", 0)),
                    "pct_change": _safe_float(row.get("今日涨跌幅", 0)),
                })
            self._cache_set(cache_key, results, CAPITAL_FLOW_TTL)
            return results
        except Exception as e:
            logger.error(f"Error fetching market capital flow: {e}")
            return []

    # ------------------------------------------------------------------
    # Peer comparison
    # ------------------------------------------------------------------
    async def fetch_peer_comparison(self, stock_code: str, limit: int = 6) -> Dict:
        """Fetch same-industry peers with key metrics for comparison."""
        cache_key = f"data:peers:{stock_code}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        try:
            # 1. Get the stock's industry via sector constituent list
            industry_name = None
            try:
                df_ind = await asyncio.to_thread(ak.stock_board_industry_cons_em, symbol="全部")
                # Find which industry our stock belongs to
                # Fallback: use the stock_individual_info_em approach
            except Exception:
                pass

            # Simpler: use stock_individual_info to get industry
            try:
                df_info = await asyncio.to_thread(ak.stock_individual_info_em, symbol=stock_code)
                for _, row in df_info.iterrows():
                    item = str(row.get("item", ""))
                    value = str(row.get("value", ""))
                    if "行业" in item:
                        industry_name = value
                        break
            except Exception as e:
                logger.warning(f"Could not get industry for {stock_code}: {e}")

            if not industry_name:
                return {"industry": "未知", "target": None, "peers": []}

            # 2. Get industry constituent stocks
            peers_data = []
            try:
                df_cons = await asyncio.to_thread(ak.stock_board_industry_cons_em, symbol=industry_name)
                if not df_cons.empty:
                    peer_codes = df_cons["代码"].tolist()[:30]  # top 30 by market cap
                else:
                    peer_codes = []
            except Exception as e:
                logger.warning(f"Could not get industry constituents for {industry_name}: {e}")
                peer_codes = []

            if not peer_codes:
                return {"industry": industry_name, "target": None, "peers": []}

            # 3. Get snapshot data for peers (reuse market snapshot)
            snapshot = await self.fetch_market_snapshot()
            snapshot_map = {_normalize_stock_code(s.get("stock_code")): s for s in snapshot}
            target_code = _normalize_stock_code(stock_code)

            target = None
            for code in peer_codes:
                norm_code = _normalize_stock_code(code)
                s = snapshot_map.get(norm_code)
                if not s:
                    continue
                item = {
                    "stock_code": s["stock_code"],
                    "stock_name": s["stock_name"],
                    "price": s.get("price", 0),
                    "pct_change": s.get("pct_change", 0),
                    "market_cap": s.get("market_cap", 0),
                    "pe": s.get("pe"),
                    "pb": s.get("pb"),
                    "turnover_rate": s.get("turnover_rate", 0),
                }
                if norm_code == target_code:
                    target = item
                else:
                    peers_data.append(item)

            # Sort peers by market cap desc, take top N
            peers_data.sort(key=lambda x: x.get("market_cap", 0) or 0, reverse=True)
            peers_data = peers_data[:limit]

            result = {
                "industry": industry_name,
                "target": target,
                "peers": peers_data,
            }
            self._cache_set(cache_key, result, SECTOR_TTL)
            return result
        except Exception as e:
            logger.error(f"Error fetching peer comparison for {stock_code}: {e}")
            return {"industry": "未知", "target": None, "peers": []}

    # ------------------------------------------------------------------
    # Stock news
    # ------------------------------------------------------------------
    async def fetch_stock_news(self, stock_code: str, limit: int = 20) -> List[Dict]:
        """Fetch recent news for a stock (cached 30min)"""
        cache_key = f"data:news:{stock_code}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached[:limit]

        try:
            df = await asyncio.to_thread(ak.stock_news_em, symbol=stock_code)
            if df.empty:
                return []

            news = []
            for _, row in df.head(limit).iterrows():
                news.append({
                    "title": str(row.get("新闻标题", "")),
                    "content": str(row.get("新闻内容", ""))[:200],
                    "publish_time": str(row.get("发布时间", "")),
                    "source": str(row.get("文章来源", "")),
                    "url": str(row.get("新闻链接", "")),
                })
            self._cache_set(cache_key, news, 1800)
            return news
        except Exception as e:
            logger.error(f"Error fetching news for {stock_code}: {e}")
            return []

    # ------------------------------------------------------------------
    # Northbound capital (沪深港通)
    # ------------------------------------------------------------------
    async def fetch_northbound_flow(self, days: int = 30) -> List[Dict]:
        """Fetch northbound (沪深港通) daily net inflow data (cached 30min)."""
        cache_key = f"data:northbound_flow:{days}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached[:days]

        try:
            df = await asyncio.to_thread(ak.stock_hsgt_north_net_flow_in_em, symbol="北向")
            if df.empty:
                return []

            rows = []
            for _, row in df.tail(days).iterrows():
                rows.append({
                    "date": str(row.get("日期", "")),
                    "net_inflow": _safe_float(row.get("当日净流入", 0)),
                    "buy_amount": _safe_float(row.get("当日买入成交额", 0)),
                    "sell_amount": _safe_float(row.get("当日卖出成交额", 0)),
                    "cumulative_net_inflow": _safe_float(row.get("历史累计净流入", 0)),
                })
            rows.reverse()  # most recent first
            self._cache_set(cache_key, rows, 1800)
            return rows
        except Exception as e:
            logger.error(f"Error fetching northbound flow: {e}")
            return []

    async def fetch_northbound_stock_holding(self, stock_code: str) -> Dict:
        """Fetch northbound holding data for a specific stock (cached 1h)."""
        cache_key = f"data:northbound_hold:{stock_code}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        try:
            df = await asyncio.to_thread(ak.stock_hsgt_individual_em, symbol=stock_code)
            if df.empty:
                return {}

            latest = df.iloc[0]
            result = {
                "stock_code": stock_code,
                "date": str(latest.get("日期", "")),
                "hold_shares": _safe_float(latest.get("持股数量", 0)),
                "hold_market_value": _safe_float(latest.get("持股市值", 0)),
                "hold_pct": _safe_float(latest.get("持股数量占A股百分比", 0)),
                "change_shares": _safe_float(latest.get("增持数量", 0)),
            }
            self._cache_set(cache_key, result, FINANCIAL_TTL)
            return result
        except Exception as e:
            logger.debug(f"Northbound holding data not available for {stock_code}: {e}")
            return {}

    # ------------------------------------------------------------------
    # Financial data
    # ------------------------------------------------------------------
    async def fetch_financial_data(self, stock_code: str, years: int = 5) -> List[Dict]:
        """Fetch financial data for a stock (cached 1h)"""
        cache_key = f"data:financial:{stock_code}:{years}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        # Primary: 同花顺 financial abstract (reliable)
        try:
            df = await asyncio.to_thread(ak.stock_financial_abstract_ths, symbol=stock_code)
            if df is not None and not df.empty:
                df = df.tail(years * 4)  # most recent records
                financials = []
                for _, row in df.iterrows():
                    financials.append({
                        "stock_code": stock_code,
                        "report_date": str(row.get("报告期", "")),
                        "eps": _safe_float(row.get("基本每股收益", 0)),
                        "roe": _safe_float(row.get("净资产收益率", 0)),
                        "revenue": _parse_cn_amount(row.get("营业总收入", 0)),
                        "net_profit": _parse_cn_amount(row.get("净利润", 0)),
                        "revenue_growth": _safe_float(row.get("营业总收入同比增长率", 0)),
                        "net_profit_growth": _safe_float(row.get("净利润同比增长率", 0)),
                        "debt_ratio": _safe_float(row.get("资产负债率", 0)),
                        "current_ratio": _safe_float(row.get("流动比率", 0)),
                        "gross_margin": _safe_float(row.get("销售毛利率", 0)),
                        "net_margin": _safe_float(row.get("销售净利率", 0)),
                    })
                self._cache_set(cache_key, financials, FINANCIAL_TTL)
                return financials
        except Exception as e:
            logger.warning(f"THS financial data failed for {stock_code}: {e}")

        # Fallback: Sina financial indicators
        try:
            df = await asyncio.to_thread(ak.stock_financial_analysis_indicator, symbol=stock_code)
            if df is not None and not df.empty:
                df = df.head(years * 4)
                financials = []
                for _, row in df.iterrows():
                    financials.append({
                        "stock_code": stock_code,
                        "report_date": str(row.get("日期", "")),
                        "eps": _safe_float(row.get("基本每股收益", 0)),
                        "roe": _safe_float(row.get("净资产收益率", 0)),
                        "revenue": 0,
                        "net_profit": 0,
                        "revenue_growth": _safe_float(row.get("营业总收入同比增长", 0)),
                        "net_profit_growth": _safe_float(row.get("净利润同比增长", 0)),
                        "debt_ratio": _safe_float(row.get("资产负债率", 0)),
                        "current_ratio": _safe_float(row.get("流动比率", 0)),
                        "gross_margin": _safe_float(row.get("销售毛利率", 0)),
                        "net_margin": _safe_float(row.get("销售净利率", 0)),
                    })
                self._cache_set(cache_key, financials, FINANCIAL_TTL)
                return financials
        except Exception as e:
            logger.error(f"Sina financial data also failed for {stock_code}: {e}")

        return []
