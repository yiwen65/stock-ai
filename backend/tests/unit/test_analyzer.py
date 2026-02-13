# backend/tests/unit/test_analyzer.py

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.engines.analyzer import StockAnalyzer
from app.schemas.analysis import AnalysisReport


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def mock_cache():
    """Mock Redis cache"""
    cache = Mock()
    cache.get = Mock(return_value=None)
    cache.setex = Mock(return_value=True)
    return cache


@pytest.fixture
def analyzer(mock_db, mock_cache):
    """Create StockAnalyzer instance with mocked dependencies"""
    return StockAnalyzer(db=mock_db, cache=mock_cache)


@pytest.mark.asyncio
async def test_analyze_returns_report(analyzer):
    """Test that analyze returns a valid AnalysisReport"""
    stock_code = "600519"

    report = await analyzer.analyze(stock_code)

    assert isinstance(report, AnalysisReport)
    assert report.stock_code == stock_code
    assert report.stock_name is not None
    assert 0 <= report.overall_score <= 10
    assert report.risk_level in ["low", "medium", "high"]
    assert report.recommendation in ["buy", "hold", "watch", "sell"]


@pytest.mark.asyncio
async def test_analyze_uses_cache(analyzer, mock_cache):
    """Test that analyze checks cache before generating new report"""
    stock_code = "600519"

    # First call - cache miss
    mock_cache.get.return_value = None
    report1 = await analyzer.analyze(stock_code)

    # Verify cache was checked
    cache_key = f"analysis:report:{stock_code}"
    mock_cache.get.assert_called()

    # Verify cache was set
    mock_cache.setex.assert_called()
    assert mock_cache.setex.call_args[0][0] == cache_key
    assert mock_cache.setex.call_args[0][1] == 3600  # TTL


@pytest.mark.asyncio
async def test_analyze_force_refresh_bypasses_cache(analyzer, mock_cache):
    """Test that force_refresh bypasses cache"""
    stock_code = "600519"

    # Call with force_refresh=True
    report = await analyzer.analyze(stock_code, force_refresh=True)

    # Cache should not be checked
    mock_cache.get.assert_not_called()

    # But result should still be cached
    mock_cache.setex.assert_called()


@pytest.mark.asyncio
async def test_calculate_overall_score(analyzer):
    """Test overall score calculation with weighted average"""
    from app.schemas.analysis import (
        FundamentalAnalysis,
        TechnicalAnalysis,
        CapitalFlowAnalysis
    )

    fundamental = FundamentalAnalysis(
        score=8.0,
        valuation={},
        profitability={},
        growth={},
        financial_health={},
        summary="Good"
    )

    technical = TechnicalAnalysis(
        score=6.0,
        trend="上涨",
        summary="OK"
    )

    capital_flow = CapitalFlowAnalysis(
        score=7.0,
        main_net_inflow=1000000.0,
        main_inflow_ratio=0.05,
        trend="流入",
        summary="Good"
    )

    overall = analyzer._calculate_overall_score(fundamental, technical, capital_flow)

    # Expected: 8.0 * 0.4 + 6.0 * 0.3 + 7.0 * 0.3 = 7.1
    assert overall == 7.1


@pytest.mark.asyncio
async def test_assess_risk_levels(analyzer):
    """Test risk level assessment"""
    assert analyzer._assess_risk(9.0) == "low"
    assert analyzer._assess_risk(7.5) == "low"
    assert analyzer._assess_risk(6.0) == "medium"
    assert analyzer._assess_risk(5.0) == "medium"
    assert analyzer._assess_risk(4.0) == "high"


@pytest.mark.asyncio
async def test_generate_recommendation(analyzer):
    """Test investment recommendation generation"""
    assert analyzer._generate_recommendation(9.0) == "buy"
    assert analyzer._generate_recommendation(8.0) == "buy"
    assert analyzer._generate_recommendation(7.0) == "hold"
    assert analyzer._generate_recommendation(6.5) == "hold"
    assert analyzer._generate_recommendation(6.0) == "watch"
    assert analyzer._generate_recommendation(5.0) == "watch"
    assert analyzer._generate_recommendation(4.0) == "sell"
