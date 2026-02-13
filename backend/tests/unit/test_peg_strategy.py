# backend/tests/unit/test_peg_strategy.py
import pytest
from unittest.mock import AsyncMock, patch
from app.engines.strategies.peg import PEGStrategy

@pytest.fixture
def peg_strategy():
    return PEGStrategy()

@pytest.fixture
def mock_stock_data():
    return [
        {
            "stock_code": "300750",
            "stock_name": "宁德时代",
            "market_cap": 8000000000,
            "pe": 30.0,
            "pb": 8.0,
            "roe": 15.5,
            "debt_ratio": 40.0
        },
        {
            "stock_code": "002594",
            "stock_name": "比亚迪",
            "market_cap": 10000000000,
            "pe": 25.0,
            "pb": 6.0,
            "roe": 18.2,
            "debt_ratio": 50.0
        },
        {
            "stock_code": "688981",
            "stock_name": "中芯国际",
            "market_cap": 6000000000,
            "pe": 40.0,
            "pb": 4.0,
            "roe": 12.0,
            "debt_ratio": 35.0
        }
    ]

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_peg_strategy_execution(mock_fetch, peg_strategy, mock_stock_data):
    """Test PEG strategy execution"""
    mock_fetch.return_value = mock_stock_data

    results = await peg_strategy.execute()

    assert isinstance(results, list)
    assert len(results) > 0

    # Verify all results meet PEG criteria
    for stock in results:
        assert stock["roe"] > 10.0
        assert stock["market_cap"] > 5000000000

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_peg_strategy_sorting(mock_fetch, peg_strategy, mock_stock_data):
    """Test that results are sorted by ROE (descending)"""
    mock_fetch.return_value = mock_stock_data

    results = await peg_strategy.execute()

    # Verify sorting by ROE (higher is better for growth)
    for i in range(len(results) - 1):
        assert results[i]["roe"] >= results[i + 1]["roe"]

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_peg_strategy_with_custom_params(mock_fetch, peg_strategy, mock_stock_data):
    """Test PEG strategy with custom parameters"""
    mock_fetch.return_value = mock_stock_data

    params = {
        "roe_min": 15.0,
        "market_cap_min": 8000000000
    }

    results = await peg_strategy.execute(params)

    # Verify all results meet custom criteria
    for stock in results:
        assert stock["roe"] >= 15.0
        assert stock["market_cap"] >= 8000000000
