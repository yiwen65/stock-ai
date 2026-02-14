# backend/app/tasks/indicator_calc.py

from celery import shared_task, group
import asyncio
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@shared_task(
    name="calculate_indicators",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def calculate_indicators(self, stock_code: str):
    """计算技术指标"""
    try:
        result = asyncio.run(_calculate_indicators(stock_code))
        return result
    except Exception as exc:
        logger.error(f"Failed to calculate indicators for {stock_code}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


async def _calculate_indicators(stock_code: str):
    """异步计算技术指标"""
    from app.utils.indicators import (
        calculate_ma, calculate_macd, calculate_rsi, calculate_kdj,
        calculate_boll, calculate_volume_ma
    )
    from app.core.database import get_influxdb

    influxdb = get_influxdb()

    # 1. 获取 K 线数据
    kline_data = await influxdb.read_kline_data(stock_code, period='1d', days=120)

    if len(kline_data) < 60:
        return "Insufficient data"

    df = pd.DataFrame(kline_data)

    # 2. 计算各类指标
    ma_data = calculate_ma(df['close'], [5, 10, 20, 60])
    macd_data = calculate_macd(df['close'])
    rsi_data = calculate_rsi(df['close'], [6, 12, 24])
    kdj_data = calculate_kdj(df['high'], df['low'], df['close'])
    boll_data = calculate_boll(df['close'])
    vol_ma_data = calculate_volume_ma(df['volume'], [5, 10, 20])

    # 3. 合并所有指标
    indicators = {
        **ma_data,
        **macd_data,
        **rsi_data,
        **kdj_data,
        **boll_data,
        **vol_ma_data
    }

    # 4. 写入 InfluxDB
    await influxdb.write_indicators(stock_code, indicators)

    return "Indicators calculated"


@shared_task(name="calculate_all_indicators")
def calculate_all_indicators():
    """批量计算所有股票的技术指标"""
    result = asyncio.run(_calculate_all_indicators())
    return result


async def _calculate_all_indicators():
    """异步批量计算所有股票的技术指标"""
    from app.services.data_service import DataService

    data_service = DataService()
    stock_codes = await data_service.get_all_stock_codes()

    # 使用 Celery group 并行执行
    job = group(
        calculate_indicators.s(code) for code in stock_codes
    )
    result = job.apply_async()

    return f"Calculating indicators for {len(stock_codes)} stocks"
