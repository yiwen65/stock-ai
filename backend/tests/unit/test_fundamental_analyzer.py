# backend/tests/unit/test_fundamental_analyzer.py

import pytest
from app.engines.fundamental_analyzer import FundamentalAnalyzer
from app.schemas.analysis import FundamentalAnalysis


@pytest.fixture
def analyzer():
    """Create FundamentalAnalyzer instance"""
    return FundamentalAnalyzer()


@pytest.mark.asyncio
async def test_analyze_returns_fundamental_analysis(analyzer):
    """Test that analyze returns a valid FundamentalAnalysis"""
    stock_code = "600519"

    result = await analyzer.analyze(stock_code)

    assert isinstance(result, FundamentalAnalysis)
    assert 0 <= result.score <= 10
    assert 'pe_ttm' in result.valuation
    assert 'roe' in result.profitability
    assert 'revenue_growth_yoy' in result.growth
    assert 'debt_ratio' in result.financial_health
    assert result.summary is not None


@pytest.mark.asyncio
async def test_analyze_valuation(analyzer):
    """Test valuation analysis"""
    stock_data = {
        'pe_ttm': 12.5,
        'pb': 1.8,
        'ps': 2.5,
        'industry': '白酒'
    }

    result = await analyzer.analyze_valuation(stock_data)

    assert 'score' in result
    assert 0 <= result['score'] <= 10
    assert result['pe_ttm'] == 12.5
    assert result['pb'] == 1.8
    assert result['ps'] == 2.5


@pytest.mark.asyncio
async def test_analyze_profitability(analyzer):
    """Test profitability analysis"""
    financials = [
        {
            'roe': 0.18,
            'roa': 0.10,
            'net_margin': 0.15,
            'gross_margin': 0.45
        },
        {
            'roe': 0.17,
            'roa': 0.09,
            'net_margin': 0.14,
            'gross_margin': 0.44
        }
    ]

    result = await analyzer.analyze_profitability(financials)

    assert 'score' in result
    assert 0 <= result['score'] <= 10
    assert result['roe'] == 0.18
    assert result['roa'] == 0.10
    assert 'roe_std' in result


@pytest.mark.asyncio
async def test_analyze_profitability_empty_data(analyzer):
    """Test profitability analysis with empty data"""
    result = await analyzer.analyze_profitability([])

    assert result['score'] == 0
    assert result['roe'] == 0
    assert result['roa'] == 0


@pytest.mark.asyncio
async def test_analyze_growth(analyzer):
    """Test growth analysis"""
    financials = [
        {'revenue': 120000000, 'net_profit': 18000000},
        {'revenue': 100000000, 'net_profit': 15000000},
        {'revenue': 90000000, 'net_profit': 13000000},
        {'revenue': 80000000, 'net_profit': 11000000}
    ]

    result = await analyzer.analyze_growth(financials)

    assert 'score' in result
    assert 0 <= result['score'] <= 10
    assert 'revenue_growth_yoy' in result
    assert 'profit_growth_yoy' in result
    assert 'revenue_cagr_3y' in result


@pytest.mark.asyncio
async def test_analyze_growth_insufficient_data(analyzer):
    """Test growth analysis with insufficient data"""
    financials = [{'revenue': 100000000, 'net_profit': 15000000}]

    result = await analyzer.analyze_growth(financials)

    assert result['score'] == 0
    assert result['revenue_growth_yoy'] == 0


@pytest.mark.asyncio
async def test_analyze_financial_health(analyzer):
    """Test financial health analysis"""
    financials = {
        'debt_ratio': 0.40,
        'current_ratio': 1.8,
        'operating_cash_flow': 20000000,
        'free_cash_flow': 12000000
    }

    result = await analyzer.analyze_financial_health(financials)

    assert 'score' in result
    assert 0 <= result['score'] <= 10
    assert result['debt_ratio'] == 0.40
    assert result['current_ratio'] == 1.8


@pytest.mark.asyncio
async def test_analyze_financial_health_empty_data(analyzer):
    """Test financial health analysis with empty data"""
    result = await analyzer.analyze_financial_health({})

    assert result['score'] == 0


def test_calculate_yoy_growth(analyzer):
    """Test YoY growth calculation"""
    # 20% growth
    growth = analyzer._calculate_yoy_growth([120, 100])
    assert growth == 0.2

    # Negative growth
    growth = analyzer._calculate_yoy_growth([80, 100])
    assert growth == -0.2

    # Zero base
    growth = analyzer._calculate_yoy_growth([100, 0])
    assert growth == 0.0


def test_calculate_cagr(analyzer):
    """Test CAGR calculation"""
    # 3-year CAGR
    values = [133.1, 121, 110, 100]
    cagr = analyzer._calculate_cagr(values)
    assert 0.10 <= cagr <= 0.11  # ~10% CAGR

    # Zero base
    cagr = analyzer._calculate_cagr([100, 90, 80, 0])
    assert cagr == 0.0


def test_valuation_score_calculation(analyzer):
    """Test valuation score calculation"""
    # Low valuation (good)
    score = analyzer._calculate_valuation_score(10, 1.5, 2.0, 20)
    assert score >= 6

    # High valuation (bad)
    score = analyzer._calculate_valuation_score(40, 6.0, 15.0, 20)
    assert score <= 5


def test_profitability_score_calculation(analyzer):
    """Test profitability score calculation"""
    # High profitability
    score = analyzer._calculate_profitability_score(0.25, 0.12, 0.20, 0.01)
    assert score >= 8

    # Low profitability
    score = analyzer._calculate_profitability_score(0.03, 0.01, 0.02, 0.10)
    assert score <= 3


def test_growth_score_calculation(analyzer):
    """Test growth score calculation"""
    # High growth
    score = analyzer._calculate_growth_score(0.35, 0.40, 0.30)
    assert score >= 8

    # Low growth
    score = analyzer._calculate_growth_score(0.02, 0.01, 0.03)
    assert score <= 4


def test_health_score_calculation(analyzer):
    """Test financial health score calculation"""
    # Healthy financials
    score = analyzer._calculate_health_score(0.25, 2.5, 50000000, 30000000)
    assert score >= 8

    # Unhealthy financials
    score = analyzer._calculate_health_score(0.80, 0.8, -10000000, -5000000)
    assert score <= 3
