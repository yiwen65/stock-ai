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
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Use Wilder's smoothing (EMA with alpha=1/period), the industry standard
        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss
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


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    计算 ATR (Average True Range)

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 周期

    Returns:
        ATR 序列
    """
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> Dict[str, pd.Series]:
    """
    计算 ADX (Average Directional Index) 趋势强度指标

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 周期

    Returns:
        包含 adx, plus_di, minus_di 的字典
    """
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)

    plus_dm = high - prev_high
    minus_dm = prev_low - low

    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.ewm(span=period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)

    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
    adx = dx.ewm(span=period, adjust=False).mean()

    return {
        'adx': adx,
        'plus_di': plus_di,
        'minus_di': minus_di
    }


def detect_ma_alignment(prices: pd.Series) -> Dict:
    """
    检测均线排列状态

    Returns:
        Dict with 'bullish' (多头排列), 'bearish' (空头排列), 'ma_values'
    """
    ma_periods = [5, 10, 20, 60]
    mas = calculate_ma(prices, ma_periods)

    latest = {k: v.iloc[-1] for k, v in mas.items() if not np.isnan(v.iloc[-1])}

    if len(latest) < 4:
        return {'bullish': False, 'bearish': False, 'ma_values': latest}

    bullish = latest['ma5'] > latest['ma10'] > latest['ma20'] > latest['ma60']
    bearish = latest['ma5'] < latest['ma10'] < latest['ma20'] < latest['ma60']

    return {
        'bullish': bullish,
        'bearish': bearish,
        'ma_values': latest
    }


def detect_macd_cross(prices: pd.Series) -> Dict:
    """
    检测 MACD 金叉/死叉

    Returns:
        Dict with 'golden_cross' (金叉), 'death_cross' (死叉), 'dif', 'dea'
    """
    macd = calculate_macd(prices)
    dif = macd['dif']
    dea = macd['dea']

    if len(dif) < 2:
        return {'golden_cross': False, 'death_cross': False, 'dif': 0, 'dea': 0}

    prev_diff = dif.iloc[-2] - dea.iloc[-2]
    curr_diff = dif.iloc[-1] - dea.iloc[-1]

    golden_cross = prev_diff <= 0 and curr_diff > 0
    death_cross = prev_diff >= 0 and curr_diff < 0

    return {
        'golden_cross': golden_cross,
        'death_cross': death_cross,
        'dif': float(dif.iloc[-1]),
        'dea': float(dea.iloc[-1]),
        'bar': float(macd['bar'].iloc[-1])
    }
