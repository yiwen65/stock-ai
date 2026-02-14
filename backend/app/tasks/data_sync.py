# backend/app/tasks/data_sync.py

from celery import shared_task, group
from datetime import datetime, time
import asyncio
import json
import logging
from app.core.alerting import alert_manager, AlertLevel

logger = logging.getLogger(__name__)


def is_trading_time() -> bool:
    """判断是否在交易时间"""
    now = datetime.now()
    weekday = now.weekday()

    # 周末不交易
    if weekday >= 5:
        return False

    # 交易时间: 9:30-11:30, 13:00-15:00
    time_now = now.time()
    morning_start = time(9, 30)
    morning_end = time(11, 30)
    afternoon_start = time(13, 0)
    afternoon_end = time(15, 0)

    return (morning_start <= time_now <= morning_end) or \
           (afternoon_start <= time_now <= afternoon_end)


@shared_task(
    name="sync_realtime_quotes",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def sync_realtime_quotes(self):
    """同步实时行情（交易时间每 3 秒执行）"""
    try:
        if not is_trading_time():
            return "Not trading time"

        result = asyncio.run(_sync_realtime_quotes())
        return result
    except Exception as exc:
        logger.error(f"Failed to sync realtime quotes: {exc}", exc_info=True)
        # 发送告警
        asyncio.run(alert_manager.send_alert(
            level=AlertLevel.ERROR,
            title="Data Sync Failed",
            message=f"Failed to sync realtime quotes: {str(exc)}",
            metadata={'task': 'sync_realtime_quotes'}
        ))
        raise self.retry(exc=exc, countdown=60)


async def _sync_realtime_quotes():
    """异步同步实时行情"""
    from app.services.data_service import DataService
    from app.core.cache import get_redis
    from app.core.database import get_influxdb

    data_service = DataService()
    redis = get_redis()
    influxdb = get_influxdb()

    # 1. 获取所有股票代码
    stock_codes = await data_service.get_all_stock_codes()

    # 2. 批量获取实时行情
    quotes = await data_service.fetch_realtime_quotes_batch(stock_codes)

    # 3. 写入 Redis（TTL: 5秒）
    for quote in quotes:
        cache_key = f"stock:realtime:{quote['stock_code']}"
        await redis.setex(cache_key, 5, json.dumps(quote))

    # 4. 写入 InfluxDB
    await influxdb.write_realtime_quotes(quotes)

    return len(quotes)


@shared_task(
    name="sync_kline_data",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def sync_kline_data(self, stock_code: str, period: str = '1d'):
    """同步 K 线数据"""
    try:
        result = asyncio.run(_sync_kline_data(stock_code, period))
        return result
    except Exception as exc:
        logger.error(f"Failed to sync kline data for {stock_code}: {exc}", exc_info=True)
        # 发送告警
        asyncio.run(alert_manager.send_alert(
            level=AlertLevel.ERROR,
            title="K-line Data Sync Failed",
            message=f"Failed to sync kline data for {stock_code}: {str(exc)}",
            metadata={'task': 'sync_kline_data', 'stock_code': stock_code, 'period': period}
        ))
        raise self.retry(exc=exc, countdown=60)


async def _sync_kline_data(stock_code: str, period: str):
    """异步同步 K 线数据"""
    from app.services.data_service import DataService
    from app.core.database import get_influxdb

    data_service = DataService()
    influxdb = get_influxdb()

    # 获取 K 线数据（最近 500 天）
    kline_data = await data_service.fetch_kline_data(
        stock_code, period=period, days=500
    )

    # 写入 InfluxDB
    await influxdb.write_kline_data(stock_code, period, kline_data)

    return len(kline_data)


@shared_task(
    name="sync_financial_data",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def sync_financial_data(self, stock_code: str):
    """同步财务数据"""
    try:
        result = asyncio.run(_sync_financial_data(stock_code))
        return result
    except Exception as exc:
        logger.error(f"Failed to sync financial data for {stock_code}: {exc}", exc_info=True)
        # 发送告警
        asyncio.run(alert_manager.send_alert(
            level=AlertLevel.ERROR,
            title="Financial Data Sync Failed",
            message=f"Failed to sync financial data for {stock_code}: {str(exc)}",
            metadata={'task': 'sync_financial_data', 'stock_code': stock_code}
        ))
        raise self.retry(exc=exc, countdown=60)


async def _sync_financial_data(stock_code: str):
    """异步同步财务数据"""
    from app.services.data_service import DataService
    from app.core.database import get_db
    from app.models.stock import StockFinancial

    data_service = DataService()
    db = next(get_db())

    try:
        # 获取财务数据（最近 5 年）
        financials = await data_service.fetch_financial_data(stock_code, years=5)

        # 写入 PostgreSQL
        for financial in financials:
            db.merge(StockFinancial(**financial))
        db.commit()

        return len(financials)
    finally:
        db.close()


@shared_task(name="sync_all_financial_data")
def sync_all_financial_data():
    """批量同步所有股票财务数据 (凌晨2:00)"""
    result = asyncio.run(_sync_all_financial_data())
    return result


async def _sync_all_financial_data():
    """异步批量同步财务数据"""
    from app.services.data_service import DataService

    data_service = DataService()
    stock_codes = await data_service.get_all_stock_codes()

    # Use Celery group for parallel financial sync
    job = group(
        sync_financial_data.s(code) for code in stock_codes[:500]
    )
    job.apply_async()

    return f"Syncing financial data for {min(len(stock_codes), 500)} stocks"


@shared_task(name="sync_all_stocks_data")
def sync_all_stocks_data():
    """批量同步所有股票数据"""
    result = asyncio.run(_sync_all_stocks_data())
    return result


async def _sync_all_stocks_data():
    """异步批量同步所有股票数据"""
    from app.services.data_service import DataService

    data_service = DataService()
    stock_codes = await data_service.get_all_stock_codes()

    # 使用 Celery group 并行执行
    job = group(
        sync_kline_data.s(code) for code in stock_codes
    )
    result = job.apply_async()

    return f"Syncing {len(stock_codes)} stocks"
