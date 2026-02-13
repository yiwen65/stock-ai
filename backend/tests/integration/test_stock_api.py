# backend/tests/integration/test_stock_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

@pytest.fixture
def mock_stock_list():
    return [
        {"stock_code": "600000", "stock_name": "浦发银行"},
        {"stock_code": "600036", "stock_name": "招商银行"},
        {"stock_code": "600519", "stock_name": "贵州茅台"}
    ]

@pytest.fixture
def mock_quote():
    return {
        "stock_code": "600519",
        "price": 1800.0,
        "change": 20.0,
        "pct_change": 1.12,
        "volume": 1000000,
        "amount": 1800000000.0,
        "high": 1820.0,
        "low": 1780.0,
        "open": 1790.0,
        "pre_close": 1780.0
    }

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_get_stocks(mock_fetch, mock_stock_list):
    """Test getting stock list"""
    mock_fetch.return_value = mock_stock_list

    response = client.get("/api/v1/stock/stocks")
    assert response.status_code == 200

    stocks = response.json()
    assert isinstance(stocks, list)
    assert len(stocks) == 3
    assert stocks[0]["stock_code"] == "600000"

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_get_stocks_empty(mock_fetch):
    """Test getting stock list when service fails"""
    mock_fetch.return_value = []

    response = client.get("/api/v1/stock/stocks")
    assert response.status_code == 503
    assert "Failed to fetch stock list" in response.json()["detail"]

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_realtime_quote')
async def test_get_stock_quote(mock_fetch, mock_quote):
    """Test getting stock quote"""
    mock_fetch.return_value = mock_quote

    response = client.get("/api/v1/stock/stocks/600519/quote")
    assert response.status_code == 200

    quote = response.json()
    assert quote["stock_code"] == "600519"
    assert quote["price"] == 1800.0
    assert quote["pct_change"] == 1.12

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_realtime_quote')
async def test_get_stock_quote_not_found(mock_fetch):
    """Test getting quote for non-existent stock"""
    mock_fetch.return_value = None

    response = client.get("/api/v1/stock/stocks/999999/quote")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
