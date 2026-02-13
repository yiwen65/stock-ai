# backend/tests/integration/test_stock_picker_flow.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

@pytest.fixture
def comprehensive_stock_data():
    """Comprehensive stock data for end-to-end testing"""
    return [
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
        },
        {
            "stock_code": "000858",
            "stock_name": "五粮液",
            "market_cap": 12000000000,
            "pe": 25.0,
            "pb": 5.0,
            "roe": 20.2,
            "debt_ratio": 30.0,
            "volume": 10000000,
            "status": "normal"
        },
        {
            "stock_code": "600000",
            "stock_name": "浦发银行",
            "market_cap": 5000000000,
            "pe": 10.5,
            "pb": 1.2,
            "roe": 12.5,
            "debt_ratio": 45.0,
            "volume": 12000000,
            "status": "normal"
        },
        {
            "stock_code": "600001",
            "stock_name": "*ST华信",
            "market_cap": 2000000000,
            "pe": 50.0,
            "pb": 3.0,
            "roe": 5.0,
            "debt_ratio": 80.0,
            "volume": 500000,
            "status": "normal"
        }
    ]

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_complete_stock_picking_flow(mock_fetch, comprehensive_stock_data):
    """Test complete stock picking flow from strategy execution to result validation"""
    mock_fetch.return_value = comprehensive_stock_data

    # 1. List available strategies
    response = client.get("/api/v1/strategies/strategies")
    assert response.status_code == 200
    strategies = response.json()
    assert len(strategies) == 5

    # 2. Execute Graham strategy
    response = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "graham",
        "limit": 10
    })
    assert response.status_code == 200
    graham_results = response.json()

    # 3. Verify Graham results meet criteria (based on available fields in response)
    for stock in graham_results:
        assert stock["pe"] < 15
        assert stock["pb"] < 2
        assert stock["market_cap"] > 5000000000

    # 4. Execute Buffett strategy
    response = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "buffett",
        "limit": 10
    })
    assert response.status_code == 200
    buffett_results = response.json()

    # 5. Verify Buffett results meet criteria (based on available fields in response)
    for stock in buffett_results:
        assert stock["roe"] > 15.0
        assert stock["market_cap"] > 10000000000

    # 6. Execute custom strategy
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
    custom_results = response.json()

    # 7. Verify custom results meet criteria
    for stock in custom_results:
        assert stock["pe"] < 20
        assert stock["roe"] > 10

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_risk_filters_applied(mock_fetch, comprehensive_stock_data):
    """Test that risk filters are automatically applied"""
    mock_fetch.return_value = comprehensive_stock_data

    # Execute strategy
    response = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "graham",
        "limit": 50
    })
    assert response.status_code == 200
    results = response.json()

    # Verify no ST stocks in results
    for stock in results:
        assert "ST" not in stock["stock_name"]

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_cache_functionality(mock_fetch, comprehensive_stock_data):
    """Test that caching works correctly"""
    mock_fetch.return_value = comprehensive_stock_data

    # First request (cache miss)
    response1 = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "graham",
        "limit": 10
    })
    assert response1.status_code == 200
    results1 = response1.json()

    # Second request (cache hit)
    response2 = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "graham",
        "limit": 10
    })
    assert response2.status_code == 200
    results2 = response2.json()

    # Results should be identical
    assert results1 == results2

    # Force refresh should bypass cache
    response3 = client.post("/api/v1/strategies/execute", json={
        "strategy_type": "graham",
        "limit": 10,
        "force_refresh": True
    })
    assert response3.status_code == 200

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_all_strategies_execution(mock_fetch, comprehensive_stock_data):
    """Test that all strategies can be executed successfully"""
    mock_fetch.return_value = comprehensive_stock_data

    strategies = ["graham", "buffett", "peg", "lynch"]

    for strategy in strategies:
        response = client.post("/api/v1/strategies/execute", json={
            "strategy_type": strategy,
            "limit": 10
        })
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

@pytest.mark.asyncio
@patch('app.services.data_service.DataService.fetch_stock_list')
async def test_limit_parameter(mock_fetch, comprehensive_stock_data):
    """Test that limit parameter works correctly"""
    # Create larger dataset
    large_dataset = comprehensive_stock_data * 20
    mock_fetch.return_value = large_dataset

    for limit in [5, 10, 20, 50]:
        response = client.post("/api/v1/strategies/execute", json={
            "strategy_type": "graham",
            "limit": limit
        })
        assert response.status_code == 200
        results = response.json()
        assert len(results) <= limit
