# backend/app/tasks/cache_warmup.py

import asyncio
from celery import shared_task
from sqlalchemy import desc
from app.core.database import SessionLocal
from app.core.cache_manager import multi_level_cache
from app.models.stock import Stock
from app.services.data_service import DataService


@shared_task(name="warmup_hot_stocks")
def warmup_hot_stocks():
    """Warmup cache for hot stocks (top 100 by volume)"""
    return asyncio.run(_warmup_hot_stocks())


async def _warmup_hot_stocks():
    """Async implementation of cache warmup"""
    db = SessionLocal()
    data_service = DataService()
    warmed_count = 0

    try:
        # Get hot stocks (top 100 by market cap as proxy for liquidity)
        hot_stocks = db.query(Stock)\
            .filter(Stock.market_cap.isnot(None))\
            .order_by(desc(Stock.market_cap))\
            .limit(100)\
            .all()

        # Batch warmup
        for stock in hot_stocks:
            try:
                # Warmup real-time quote
                realtime = await data_service.fetch_realtime_quote(stock.code)
                if realtime:
                    await multi_level_cache.set(
                        f"stock:realtime:{stock.code}",
                        realtime,
                        ttl=5  # 5 seconds for real-time data
                    )

                # Warmup basic stock info
                stock_info = {
                    "code": stock.code,
                    "name": stock.name,
                    "industry": stock.industry,
                    "market_cap": stock.market_cap,
                    "pe_ttm": stock.pe_ttm,
                    "pb": stock.pb
                }
                await multi_level_cache.set(
                    f"stock:info:{stock.code}",
                    stock_info,
                    ttl=3600  # 1 hour
                )

                warmed_count += 1

            except Exception as e:
                print(f"Failed to warmup stock {stock.code}: {e}")
                continue

        return {
            "status": "success",
            "warmed_count": warmed_count,
            "total_stocks": len(hot_stocks)
        }

    except Exception as e:
        print(f"Cache warmup failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "warmed_count": warmed_count
        }
    finally:
        db.close()


@shared_task(name="warmup_market_overview")
def warmup_market_overview():
    """Warmup cache for market overview data"""
    return asyncio.run(_warmup_market_overview())


async def _warmup_market_overview():
    """Warmup market indices and overview statistics"""
    data_service = DataService()

    try:
        # Warmup major indices (Shanghai, Shenzhen, ChiNext)
        indices = ["000001", "399001", "399006"]  # 上证指数, 深证成指, 创业板指

        for index_code in indices:
            try:
                index_data = await data_service.fetch_realtime_quote(index_code)
                if index_data:
                    await multi_level_cache.set(
                        f"index:realtime:{index_code}",
                        index_data,
                        ttl=5
                    )
            except Exception as e:
                print(f"Failed to warmup index {index_code}: {e}")

        return {"status": "success", "indices_warmed": len(indices)}

    except Exception as e:
        print(f"Market overview warmup failed: {e}")
        return {"status": "error", "error": str(e)}
