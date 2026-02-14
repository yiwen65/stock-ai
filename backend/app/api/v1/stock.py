# backend/app/api/v1/stock.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas.stock import StockResponse, QuoteResponse, KLineItem
from app.services.data_service import DataService

router = APIRouter()
data_service = DataService()


@router.get("/stocks", response_model=List[StockResponse])
async def get_stocks():
    """Get list of all A-share stocks"""
    stocks = await data_service.fetch_stock_list()
    if not stocks:
        raise HTTPException(status_code=503, detail="Failed to fetch stock list")
    return stocks


@router.get("/stocks/search", response_model=List[QuoteResponse])
async def search_stocks(
    q: str = Query(..., min_length=1, description="搜索关键词 (代码/名称)"),
    limit: int = Query(10, ge=1, le=50)
):
    """Search stocks by code or name"""
    stocks = await data_service.fetch_stock_list()
    if not stocks:
        raise HTTPException(status_code=503, detail="Failed to fetch stock list")

    keyword = q.strip().upper()
    matches = [
        s for s in stocks
        if keyword in s['stock_code'].upper() or keyword in s['stock_name'].upper()
    ][:limit]

    if not matches:
        return []

    # Try to enrich with cached snapshot (instant, no API call)
    codes = {m['stock_code'] for m in matches}
    snapshot = data_service.get_cached_snapshot()
    if snapshot:
        snapshot_map = {s.get("stock_code"): s for s in snapshot}
        enriched = [snapshot_map[c] for c in codes if c in snapshot_map]
        if enriched:
            return enriched

    # Fallback: return matches with default quote fields (always fast)
    return [
        {
            "stock_code": m["stock_code"],
            "stock_name": m["stock_name"],
            "price": 0.0,
            "change": 0.0,
            "pct_change": 0.0,
            "volume": 0,
            "amount": 0.0,
            "high": 0.0,
            "low": 0.0,
            "open": 0.0,
            "pre_close": 0.0,
        }
        for m in matches
    ]


@router.get("/stocks/{stock_code}/quote", response_model=QuoteResponse)
async def get_stock_quote(stock_code: str):
    """Get real-time quote for a specific stock"""
    quote = await data_service.fetch_realtime_quote(stock_code)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Stock {stock_code} not found")
    return quote


@router.get("/stocks/{stock_code}/kline", response_model=List[KLineItem])
async def get_stock_kline(
    stock_code: str,
    period: str = Query("1d", regex="^(1d|1w|1M)$", description="K线周期"),
    days: int = Query(250, ge=30, le=1000, description="获取天数"),
):
    """Get K-line data for a stock"""
    kline = await data_service.fetch_kline_data(stock_code, period=period, days=days)
    if not kline:
        raise HTTPException(status_code=404, detail=f"K-line data not found for {stock_code}")
    return kline


@router.get("/stocks/{stock_code}/financial")
async def get_stock_financial(
    stock_code: str,
    years: int = Query(5, ge=1, le=10, description="获取年数"),
):
    """Get historical financial indicator data for a stock"""
    data = await data_service.fetch_financial_data(stock_code, years=years)
    if not data:
        raise HTTPException(status_code=404, detail=f"Financial data not found for {stock_code}")
    return data


@router.get("/stocks/{stock_code}/news")
async def get_stock_news(
    stock_code: str,
    limit: int = Query(20, ge=1, le=50, description="新闻条数"),
):
    """Get recent news for a stock"""
    news = await data_service.fetch_stock_news(stock_code, limit=limit)
    return news


@router.get("/stocks/{stock_code}/peers")
async def get_stock_peers(
    stock_code: str,
    limit: int = Query(6, ge=1, le=20, description="同行数量"),
):
    """Get same-industry peer comparison data"""
    data = await data_service.fetch_peer_comparison(stock_code, limit=limit)
    return data


@router.get("/market/capital-flow")
async def get_market_capital_flow():
    """Get market-level capital flow by sector"""
    data = await data_service.fetch_market_capital_flow()
    return data


@router.get("/market/sectors")
async def get_sectors():
    """Get industry sector list with performance"""
    sectors = await data_service.fetch_sector_list()
    if not sectors:
        raise HTTPException(status_code=503, detail="Failed to fetch sector data")
    return sectors


@router.get("/market/indices")
async def get_market_indices():
    """Get major market index data (上证/深证/创业板/沪深300)"""
    try:
        import akshare as ak
        import logging
        logger = logging.getLogger(__name__)

        indices = [
            {"code": "000001", "name": "上证指数"},
            {"code": "399001", "name": "深证成指"},
            {"code": "399006", "name": "创业板指"},
            {"code": "000300", "name": "沪深300"},
        ]

        results = []
        try:
            df = ak.stock_zh_index_spot_em()
            for idx in indices:
                row = df[df["代码"] == idx["code"]]
                if row.empty:
                    continue
                r = row.iloc[0]
                results.append({
                    "code": idx["code"],
                    "name": idx["name"],
                    "price": float(r.get("最新价", 0)),
                    "change": float(r.get("涨跌额", 0)),
                    "pct_change": float(r.get("涨跌幅", 0)),
                    "open": float(r.get("今开", 0)),
                    "high": float(r.get("最高", 0)),
                    "low": float(r.get("最低", 0)),
                    "volume": float(r.get("成交量", 0)),
                    "amount": float(r.get("成交额", 0)),
                })
        except Exception as e:
            logger.warning(f"Failed to fetch indices: {e}")

        return results
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch index data: {str(e)}")
