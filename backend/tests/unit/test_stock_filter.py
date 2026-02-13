# backend/tests/unit/test_stock_filter.py
import pytest
from unittest.mock import patch
from app.engines.stock_filter import StockFilter
from app.schemas.strategy import FilterCondition, ConditionOperator

@pytest.fixture
def mock_stock_data():
    return [
        {
            "stock_code": "600000",
            "stock_name": "浦发银行",
            "market_cap": 5000000000,
            "pe": 10.5,
            "pb": 1.2,
            "roe": 12.5,
            "debt_ratio": 45.0,
            "volume": 10000000,
            "status": "normal"
        },
        {
            "stock_code": "600036",
            "stock_name": "招商银行",
            "market_cap": 12000000000,
            "pe": 8.5,
            "pb": 1.5,
            "roe": 15.2,
            "debt_ratio": 50.0,
            "volume": 15000000,
            "status": "normal"
        },
        {
            "stock_code": "600519",
            "stock_name": "贵州茅台",
            "market_cap": 25000000000,
            "pe": 35.0,
            "pb": 10.0,
            "roe": 25.0,
            "debt_ratio": 20.0,
            "volume": 8000000,
            "status": "normal"
        }
    ]

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_filter_by_pe(mock_fetch, mock_stock_data):
    mock_fetch.return_value = mock_stock_data

    filter_engine = StockFilter()
    condition = FilterCondition(field="pe", operator=ConditionOperator.LT, value=15.0)

    stocks = await filter_engine.apply_filter([condition])

    assert isinstance(stocks, list)
    assert len(stocks) == 2  # Only 浦发银行 and 招商银行
    assert all(stock.get("pe", 999) < 15.0 for stock in stocks if stock.get("pe"))

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_filter_multiple_conditions(mock_fetch, mock_stock_data):
    mock_fetch.return_value = mock_stock_data

    filter_engine = StockFilter()
    conditions = [
        FilterCondition(field="pe", operator=ConditionOperator.LT, value=15.0),
        FilterCondition(field="pb", operator=ConditionOperator.LT, value=2.0),
    ]

    stocks = await filter_engine.apply_filter(conditions)

    assert isinstance(stocks, list)
    for stock in stocks:
        if stock.get("pe"):
            assert stock["pe"] < 15.0
        if stock.get("pb"):
            assert stock["pb"] < 2.0
