# backend/tests/unit/test_buffett_strategy.py
import pytest
from unittest.mock import AsyncMock, patch
from app.engines.strategies.buffett import BuffettStrategy

@pytest.fixture
def buffett_strategy():
    return BuffettStrategy()

@pytest.fixture
def mock_stock_data():
    return [
        {
            "stock_code": "600036",
            "stock_name": "招商银行",
            "market_cap": 15000000000,
            "pe": 10.0,
            "pb": 1.5,
            "roe": 18.5,
            "debt_ratio": 45.0
        },
        {
            "stock_code": "000858",
            "stock_name": "五粮液",
            "market_cap": 12000000000,
            "pe": 25.0,
            "pb": 5.0,
            "roe": 20.2,
            "debt_ratio": 30.0
        },
        {
            "stock_code": "600519",
            "stock_name": "贵州茅台",
            "market_cap": 25000000000,
            "pe": 35.0,
            "pb": 10.0,
            "roe": 25.0,
            "debt_ratio": 20.0
        }
    ]

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_buffett_strategy_execution(mock_fetch, buffett_strategy, mock_stock_data):
    """Test Buffett strategy execution"""
    mock_fetch.return_value = mock_stock_data

    results = await buffett_strategy.execute()

    assert isinstance(results, list)
    assert len(results) > 0

    # Verify all results meet Buffett criteria
    for stock in results:
        assert stock["roe"] > 15.0
        assert stock["debt_ratio"] < 50.0
        assert stock["market_cap"] > 10000000000

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_buffett_strategy_sorting(mock_fetch, buffett_strategy, mock_stock_data):
    """Test that results are sorted by ROE (descending)"""
    mock_fetch.return_value = mock_stock_data

    results = await buffett_strategy.execute()

    # Verify sorting by ROE (higher is better)
    for i in range(len(results) - 1):
        assert results[i]["roe"] >= results[i + 1]["roe"]

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_buffett_strategy_with_custom_params(mock_fetch, buffett_strategy, mock_stock_data):
    """Test Buffett strategy with custom parameters"""
    mock_fetch.return_value = mock_stock_data

    params = {
        "roe_min": 20.0,
        "debt_max": 40.0,
        "market_cap_min": 12000000000
    }

    results = await buffett_strategy.execute(params)

    # Verify all results meet custom criteria
    for stock in results:
        assert stock["roe"] >= 20.0
        assert stock["debt_ratio"] < 40.0
        assert stock["market_cap"] >= 12000000000
