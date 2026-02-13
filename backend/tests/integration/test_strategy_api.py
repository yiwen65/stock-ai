# backend/tests/integration/test_strategy_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

@pytest.fixture
def mock_stock_data():
    """Mock stock data for testing"""
    return [
        {
            "stock_code": "600000",
            "stock_name": "浦发银行",
            "market_cap": 5000000000,
            "pe": 10.5,
            "pb": 1.2,
            "roe": 12.5,
            "debt_ratio": 45.0,
            "score": None
        },
        {
            "stock_code": "600036",
            "stock_name": "招商银行",
            "market_cap": 12000000000,
            "pe": 8.5,
            "pb": 1.5,
            "roe": 15.2,
            "debt_ratio": 50.0,
            "score": None
        },
        {
            "stock_code": "000001",
            "stock_name": "平安银行",
            "market_cap": 8000000000,
            "pe": 12.0,
            "pb": 1.8,
            "roe": 10.5,
            "debt_ratio": 55.0,
            "score": None
        }
    ]

@pytest.mark.asyncio
async def test_list_strategies():
    """Test listing available strategies"""
    response = client.get("/api/v1/strategies/strategies")
    assert response.status_code == 200

    strategies = response.json()
    assert len(strategies) == 5

    strategy_names = [s["name"] for s in strategies]
    assert "graham" in strategy_names
    assert "buffett" in strategy_names
    assert "peg" in strategy_names
    assert "lynch" in strategy_names
    assert "custom" in strategy_names

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_execute_graham_strategy(mock_fetch, mock_stock_data):
    """Test executing Graham value strategy"""
    mock_fetch.return_value = mock_stock_data

    response = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "graham",
        "limit": 10
    })

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10

    # Verify all results meet Graham criteria
    for stock in data:
        assert stock["pe"] < 15
        assert stock["pb"] < 2
        assert stock["market_cap"] > 5000000000

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_execute_custom_strategy(mock_fetch, mock_stock_data):
    """Test executing custom strategy"""
    mock_fetch.return_value = mock_stock_data

    response = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "custom",
        "conditions": {
            "conditions": [
                {"field": "pe", "operator": "<", "value": 20},
                {"field": "roe", "operator": ">", "value": 10}
            ],
            "logic": "AND"
        },
        "limit": 20
    })

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 20

@pytest.mark.asyncio
async def test_execute_custom_strategy_without_conditions():
    """Test that custom strategy requires conditions"""
    response = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "custom",
        "limit": 10
    })

    assert response.status_code == 400  # Business logic error

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_execute_buffett_strategy(mock_fetch, mock_stock_data):
    """Test executing Buffett moat strategy"""
    mock_fetch.return_value = mock_stock_data

    response = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "buffett",
        "limit": 10
    })

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_execute_peg_strategy(mock_fetch, mock_stock_data):
    """Test executing PEG growth strategy"""
    mock_fetch.return_value = mock_stock_data

    response = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "peg",
        "limit": 10
    })

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_execute_lynch_strategy(mock_fetch, mock_stock_data):
    """Test executing Lynch growth strategy"""
    mock_fetch.return_value = mock_stock_data

    response = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "lynch",
        "limit": 10
    })

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_execute_strategy_with_limit(mock_fetch, mock_stock_data):
    """Test strategy execution respects limit parameter"""
    # Create larger dataset
    large_dataset = mock_stock_data * 20
    mock_fetch.return_value = large_dataset

    response = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "graham",
        "limit": 5
    })

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5
