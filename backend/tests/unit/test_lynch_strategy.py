# backend/tests/unit/test_lynch_strategy.py
import pytest
from unittest.mock import AsyncMock, patch
from app.engines.strategies.lynch import LynchStrategy

@pytest.fixture
def lynch_strategy():
    return LynchStrategy()

@pytest.fixture
def mock_stock_data():
    return [
        {
            "stock_code": "002475",
            "stock_name": "立讯精密",
            "market_cap": 5000000000,
            "pe": 18.0,
            "pb": 3.5,
            "roe": 16.0,
            "debt_ratio": 55.0
        },
        {
            "stock_code": "300059",
            "stock_name": "东方财富",
            "market_cap": 4000000000,
            "pe": 15.0,
            "pb": 2.8,
            "roe": 14.5,
            "debt_ratio": 45.0
        },
        {
            "stock_code": "000333",
            "stock_name": "美的集团",
            "market_cap": 6000000000,
            "pe": 12.0,
            "pb": 2.0,
            "roe": 18.0,
            "debt_ratio": 50.0
        }
    ]

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_lynch_strategy_execution(mock_fetch, lynch_strategy, mock_stock_data):
    """Test Lynch strategy execution"""
    mock_fetch.return_value = mock_stock_data

    results = await lynch_strategy.execute()

    assert isinstance(results, list)
    assert len(results) > 0

    # Verify all results meet Lynch criteria
    for stock in results:
        assert stock["pe"] < 20.0
        assert stock["debt_ratio"] < 60.0
        assert stock["market_cap"] > 3000000000

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_lynch_strategy_sorting(mock_fetch, lynch_strategy, mock_stock_data):
    """Test that results are sorted by PE (ascending)"""
    mock_fetch.return_value = mock_stock_data

    results = await lynch_strategy.execute()

    # Verify sorting by PE (lower is better)
    for i in range(len(results) - 1):
        assert results[i]["pe"] <= results[i + 1]["pe"]

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_lynch_strategy_with_custom_params(mock_fetch, lynch_strategy, mock_stock_data):
    """Test Lynch strategy with custom parameters"""
    mock_fetch.return_value = mock_stock_data

    params = {
        "pe_max": 15.0,
        "debt_max": 50.0,
        "market_cap_min": 5000000000
    }

    results = await lynch_strategy.execute(params)

    # Verify all results meet custom criteria
    for stock in results:
        assert stock["pe"] < 15.0
        assert stock["debt_ratio"] < 50.0
        assert stock["market_cap"] >= 5000000000
