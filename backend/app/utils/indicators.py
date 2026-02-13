# backend/app/utils/indicators.py

import pandas as pd
import numpy as np
from typing import Dict, List


def calculate_ma(prices: pd.Series, periods: List[int]) -> Dict[str, pd.Series]:
    """
    计算移动平均线

    Args:
        prices: 收盘价序列
        periods: 周期列表，如 [5, 10, 20, 60]

    Returns:
        各周期的 MA 值字典
    """
    return {
        f'ma{period}': prices.rolling(window=period).mean()
        for period in periods
    }


def calculate_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, pd.Series]:
    """
    计算 MACD 指标

    Args:
        prices: 收盘价序列
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期

    Returns:
        包含 DIF, DEA, BAR 的字典
    """
    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()

    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal_period, adjust=False).mean()
    bar = (dif - dea) * 2

    return {
        'dif': dif,
        'dea': dea,
        'bar': bar
    }


def calculate_rsi(prices: pd.Series, periods: List[int]) -> Dict[str, pd.Series]:
    """
    计算 RSI 指标

    Args:
        prices: 收盘价序列
        periods: 周期列表，如 [6, 12, 24]

    Returns:
        各周期的 RSI 值字典
    """
    result = {}

    for period in periods:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        result[f'rsi{period}'] = rsi

    return result


def calculate_kdj(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    n: int = 9,
    m1: int = 3,
    m2: int = 3
) -> Dict[str, pd.Series]:
    """
    计算 KDJ 指标

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        n: RSV 周期
        m1: K 值平滑周期
        m2: D 值平滑周期

    Returns:
        包含 K, D, J 的字典
    """
    # 计算 RSV
    low_n = low.rolling(window=n).min()
    high_n = high.rolling(window=n).max()
    rsv = (close - low_n) / (high_n - low_n) * 100

    # 计算 K, D, J
    k = rsv.ewm(com=m1 - 1, adjust=False).mean()
    d = k.ewm(com=m2 - 1, adjust=False).mean()
    j = 3 * k - 2 * d

    return {
        'k': k,
        'd': d,
        'j': j
    }


def calculate_boll(
    prices: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Dict[str, pd.Series]:
    """
    计算布林带指标

    Args:
        prices: 收盘价序列
        period: 周期
        std_dev: 标准差倍数

    Returns:
        包含 upper, mid, lower 的字典
    """
    mid = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()

    upper = mid + (std * std_dev)
    lower = mid - (std * std_dev)

    return {
        'upper': upper,
        'mid': mid,
        'lower': lower
    }


def calculate_volume_ma(volume: pd.Series, periods: List[int]) -> Dict[str, pd.Series]:
    """
    计算成交量移动平均

    Args:
        volume: 成交量序列
        periods: 周期列表

    Returns:
        各周期的成交量 MA 字典
    """
    return {
        f'vol_ma{period}': volume.rolling(window=period).mean()
        for period in periods
    }
