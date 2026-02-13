# backend/tests/integration/test_analysis_api.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from main import app

client = TestClient(app)


@pytest.fixture
def mock_analyzer():
    """Mock StockAnalyzer for testing"""
    with patch('app.api.v1.analysis.StockAnalyzer') as mock:
        analyzer_instance = Mock()
        analyzer_instance.analyze = AsyncMock(return_value=Mock(
            stock_code="600519",
            stock_name="贵州茅台",
            fundamental=Mock(
                score=8.5,
                valuation={'pe_ttm': 30.0, 'pb': 10.0, 'ps': 15.0},
                profitability={'roe': 0.30, 'roa': 0.25, 'net_margin': 0.50},
                growth={'revenue_growth_yoy': 0.15, 'profit_growth_yoy': 0.18},
                financial_health={'debt_ratio': 0.20, 'current_ratio': 3.0},
                summary="基本面优秀"
            ),
            technical=Mock(
                score=7.0,
                trend="上涨",
                support_levels=[1800.0, 1750.0, 1700.0],
                resistance_levels=[1900.0, 1950.0, 2000.0],
                indicators={'ma5': 1850.0, 'ma10': 1820.0},
                summary="技术面良好"
            ),
            capital_flow=Mock(
                score=7.5,
                main_net_inflow=50000000.0,
                main_inflow_ratio=0.08,
                trend="流入",
                summary="资金面良好"
            ),
            overall_score=7.8,
            risk_level="low",
            recommendation="buy",
            summary="综合分析：值得关注",
            generated_at=1707753600,
            model_dump=lambda: {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "fundamental": {
                    "score": 8.5,
                    "valuation": {'pe_ttm': 30.0, 'pb': 10.0, 'ps': 15.0},
                    "profitability": {'roe': 0.30, 'roa': 0.25, 'net_margin': 0.50},
                    "growth": {'revenue_growth_yoy': 0.15, 'profit_growth_yoy': 0.18},
                    "financial_health": {'debt_ratio': 0.20, 'current_ratio': 3.0},
                    "summary": "基本面优秀"
                },
                "technical": {
                    "score": 7.0,
                    "trend": "上涨",
                    "support_levels": [1800.0, 1750.0, 1700.0],
                    "resistance_levels": [1900.0, 1950.0, 2000.0],
                    "indicators": {'ma5': 1850.0, 'ma10': 1820.0},
                    "summary": "技术面良好"
                },
                "capital_flow": {
                    "score": 7.5,
                    "main_net_inflow": 50000000.0,
                    "main_inflow_ratio": 0.08,
                    "trend": "流入",
                    "summary": "资金面良好"
                },
                "overall_score": 7.8,
                "risk_level": "low",
                "recommendation": "buy",
                "summary": "综合分析：值得关注",
                "generated_at": 1707753600
            }
        ))
        mock.return_value = analyzer_instance
        yield mock


def test_analyze_stock_comprehensive(mock_analyzer):
    """Test comprehensive stock analysis"""
    response = client.post("/api/v1/stocks/600519/analyze")

    assert response.status_code == 200
    data = response.json()

    assert data["stock_code"] == "600519"
    assert data["stock_name"] == "贵州茅台"
    assert "fundamental" in data
    assert "technical" in data
    assert "capital_flow" in data
    assert data["overall_score"] == 7.8
    assert data["risk_level"] == "low"
    assert data["recommendation"] == "buy"


def test_analyze_stock_with_report_type(mock_analyzer):
    """Test stock analysis with specific report type"""
    response = client.post(
        "/api/v1/stocks/600519/analyze",
        params={"report_type": "fundamental"}
    )

    assert response.status_code == 200
    mock_analyzer.return_value.analyze.assert_called_once()
    call_args = mock_analyzer.return_value.analyze.call_args
    assert call_args[0][1] == "fundamental"


def test_analyze_stock_with_force_refresh(mock_analyzer):
    """Test stock analysis with force refresh"""
    response = client.post(
        "/api/v1/stocks/600519/analyze",
        params={"force_refresh": True}
    )

    assert response.status_code == 200
    mock_analyzer.return_value.analyze.assert_called_once()
    call_args = mock_analyzer.return_value.analyze.call_args
    assert call_args[0][2] is True


def test_analyze_stock_invalid_report_type():
    """Test stock analysis with invalid report type"""
    response = client.post(
        "/api/v1/stocks/600519/analyze",
        params={"report_type": "invalid"}
    )

    assert response.status_code == 422  # Validation error


def test_get_cached_report():
    """Test retrieving cached analysis report"""
    from app.core.cache import get_cache

    # Mock cache to return a report
    mock_cache = Mock()
    mock_cache.get.return_value = '{"stock_code": "600519", "stock_name": "贵州茅台", "fundamental": {"score": 8.5, "valuation": {}, "profitability": {}, "growth": {}, "financial_health": {}, "summary": "test"}, "technical": {"score": 7.0, "trend": "上涨", "support_levels": [], "resistance_levels": [], "indicators": {}, "summary": "test"}, "capital_flow": {"score": 7.5, "main_net_inflow": 50000000.0, "main_inflow_ratio": 0.08, "trend": "流入", "summary": "test"}, "overall_score": 7.8, "risk_level": "low", "recommendation": "buy", "summary": "test", "generated_at": 1707753600}'

    # Override dependency
    app.dependency_overrides[get_cache] = lambda: mock_cache

    try:
        response = client.get("/api/v1/stocks/600519/report")

        assert response.status_code == 200
        data = response.json()
        assert data["stock_code"] == "600519"
    finally:
        # Clean up override
        app.dependency_overrides.clear()


def test_get_cached_report_not_found():
    """Test retrieving non-existent cached report"""
    from app.core.cache import get_cache

    mock_cache = Mock()
    mock_cache.get.return_value = None

    # Override dependency
    app.dependency_overrides[get_cache] = lambda: mock_cache

    try:
        response = client.get("/api/v1/stocks/999999/report")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        # Clean up override
        app.dependency_overrides.clear()


def test_analyze_stock_error_handling(mock_analyzer):
    """Test error handling in stock analysis"""
    mock_analyzer.return_value.analyze.side_effect = Exception("Database error")

    response = client.post("/api/v1/stocks/600519/analyze")

    assert response.status_code == 500
    assert "Analysis failed" in response.json()["detail"]
