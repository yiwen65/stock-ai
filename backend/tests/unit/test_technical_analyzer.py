# backend/tests/unit/test_technical_analyzer.py

import pytest
import pandas as pd
import numpy as np
from app.engines.technical_analyzer import TechnicalAnalyzer
from app.schemas.analysis import TechnicalAnalysis


@pytest.fixture
def analyzer():
    """Create TechnicalAnalyzer instance"""
    return TechnicalAnalyzer()


@pytest.fixture
def sample_kline_data():
    """Create sample K-line data for testing"""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=90, freq='D')
    np.random.seed(42)

    base_price = 100.0
    prices = base_price + np.cumsum(np.random.randn(90) * 2)

    return pd.DataFrame({
        'date': dates,
        'open': prices + np.random.randn(90) * 0.5,
        'high': prices + np.abs(np.random.randn(90) * 1.5),
        'low': prices - np.abs(np.random.randn(90) * 1.5),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 90)
    })


@pytest.mark.asyncio
async def test_analyze_returns_technical_analysis(analyzer):
    """Test that analyze returns a valid TechnicalAnalysis"""
    stock_code = "600519"

    result = await analyzer.analyze(stock_code)

    assert isinstance(result, TechnicalAnalysis)
    assert 0 <= result.score <= 10
    assert result.trend in ["强势上涨", "上涨", "震荡", "下跌", "强势下跌"]
    assert isinstance(result.support_levels, list)
    assert isinstance(result.resistance_levels, list)
    assert 'ma' in result.indicators
    assert 'macd' in result.indicators
    assert 'rsi' in result.indicators
    assert 'kdj' in result.indicators


@pytest.mark.asyncio
async def test_analyze_trend(analyzer, sample_kline_data):
    """Test trend analysis"""
    result = await analyzer.analyze_trend(sample_kline_data)

    assert 'trend' in result
    assert 'score' in result
    assert 'ma_data' in result
    assert 0 <= result['score'] <= 10
    assert result['trend'] in ["强势上涨", "上涨", "震荡", "下跌", "强势下跌"]


@pytest.mark.asyncio
async def test_analyze_momentum(analyzer, sample_kline_data):
    """Test momentum analysis"""
    result = await analyzer.analyze_momentum(sample_kline_data)

    assert 'macd' in result
    assert 'rsi' in result
    assert 'kdj' in result
    assert 'score' in result
    assert 0 <= result['score'] <= 10


@pytest.mark.asyncio
async def test_find_support_resistance(analyzer, sample_kline_data):
    """Test support and resistance level detection"""
    result = await analyzer.find_support_resistance(sample_kline_data)

    assert 'support_levels' in result
    assert 'resistance_levels' in result
    assert len(result['support_levels']) <= 3
    assert len(result['resistance_levels']) <= 3


def test_interpret_macd_golden_cross(analyzer):
    """Test MACD golden cross interpretation"""
    # Create golden cross scenario (DIF > DEA, both positive)
    macd_data = {
        'dif': pd.Series([0.5]),
        'dea': pd.Series([0.3]),
        'bar': pd.Series([0.4])
    }

    result = analyzer._interpret_macd(macd_data)

    assert result['signal'] == "强势金叉"
    assert result['score'] >= 7


def test_interpret_macd_death_cross(analyzer):
    """Test MACD death cross interpretation"""
    # Create death cross scenario (DIF < DEA, both negative)
    macd_data = {
        'dif': pd.Series([-0.5]),
        'dea': pd.Series([-0.3]),
        'bar': pd.Series([-0.4])
    }

    result = analyzer._interpret_macd(macd_data)

    assert result['signal'] == "强势死叉"
    assert result['score'] <= 4


def test_interpret_rsi_overbought(analyzer):
    """Test RSI overbought interpretation"""
    rsi_data = {
        'rsi6': pd.Series([85.0]),
        'rsi12': pd.Series([80.0]),
        'rsi24': pd.Series([75.0])
    }

    result = analyzer._interpret_rsi(rsi_data)

    assert result['signal'] == "严重超买"
    assert result['score'] <= 4


def test_interpret_rsi_oversold(analyzer):
    """Test RSI oversold interpretation"""
    rsi_data = {
        'rsi6': pd.Series([15.0]),
        'rsi12': pd.Series([20.0]),
        'rsi24': pd.Series([25.0])
    }

    result = analyzer._interpret_rsi(rsi_data)

    assert result['signal'] == "严重超卖"
    assert result['score'] >= 6


def test_interpret_kdj_golden_cross(analyzer):
    """Test KDJ golden cross interpretation"""
    kdj_data = {
        'k': pd.Series([60.0]),
        'd': pd.Series([50.0]),
        'j': pd.Series([70.0])
    }

    result = analyzer._interpret_kdj(kdj_data)

    assert result['signal'] == "强势金叉"
    assert result['score'] >= 7


def test_interpret_kdj_death_cross(analyzer):
    """Test KDJ death cross interpretation"""
    kdj_data = {
        'k': pd.Series([40.0]),
        'd': pd.Series([50.0]),
        'j': pd.Series([30.0])
    }

    result = analyzer._interpret_kdj(kdj_data)

    assert result['signal'] == "强势死叉"
    assert result['score'] <= 4


def test_find_local_minima(analyzer):
    """Test local minima detection"""
    # Create series with clear local minima
    series = pd.Series([100, 95, 90, 85, 90, 95, 100, 95, 90, 95, 100])

    minima = analyzer._find_local_minima(series, window=2)

    assert len(minima) > 0
    assert 85 in minima  # Clear minimum at index 3


def test_find_local_maxima(analyzer):
    """Test local maxima detection"""
    # Create series with clear local maxima
    series = pd.Series([100, 105, 110, 115, 110, 105, 100, 105, 110, 105, 100])

    maxima = analyzer._find_local_maxima(series, window=2)

    assert len(maxima) > 0
    assert 115 in maxima  # Clear maximum at index 3


def test_serialize_ma_data(analyzer):
    """Test MA data serialization"""
    ma_data = {
        'ma5': pd.Series([100.0, 101.0, 102.0]),
        'ma10': pd.Series([99.0, 100.0, 101.0])
    }

    result = analyzer._serialize_ma_data(ma_data)

    assert isinstance(result, dict)
    assert result['ma5'] == 102.0
    assert result['ma10'] == 101.0


def test_serialize_indicator(analyzer):
    """Test indicator data serialization"""
    indicator_data = {
        'dif': pd.Series([0.5, 0.6, 0.7]),
        'dea': pd.Series([0.4, 0.5, 0.6])
    }

    result = analyzer._serialize_indicator(indicator_data)

    assert isinstance(result, dict)
    assert result['dif'] == 0.7
    assert result['dea'] == 0.6
