# backend/tests/unit/test_graham_strategy.py
import pytest
from unittest.mock import AsyncMock, patch
from app.engines.strategies.graham import GrahamStrategy

@pytest.mark.asyncio
async def test_graham_strategy_execution():
    # Mock stock data
    mock_stocks = [
        {"stock_code": "600519", "stock_name": "贵州茅台", "pe": 30, "pb": 10, "debt_ratio": 20, "market_cap": 20000000000, "is_st": False, "is_suspended": False, "volume": 5000000},
        {"stock_code": "000858", "stock_name": "五粮液", "pe": 12, "pb": 1.5, "debt_ratio": 30, "market_cap": 8000000000, "is_st": False, "is_suspended": False, "volume": 3000000},
        {"stock_code": "600036", "stock_name": "招商银行", "pe": 8, "pb": 0.9, "debt_ratio": 50, "market_cap": 15000000000, "is_st": False, "is_suspended": False, "volume": 10000000},
        {"stock_code": "601318", "stock_name": "中国平安", "pe": 10, "pb": 1.2, "debt_ratio": 40, "market_cap": 12000000000, "is_st": False, "is_suspended": False, "volume": 8000000},
    ]

    with patch('app.services.data_service.DataService.fetch_stock_list', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_stocks

        strategy = GrahamStrategy()
        results = await strategy.execute()

        assert isinstance(results, list)
        assert len(results) > 0

        # Verify Graham criteria (PE < 15, PB < 2, debt_ratio < 60)
        for stock in results:
            assert stock.get("pe", 999) < 15
            assert stock.get("pb", 999) < 2
            assert stock.get("debt_ratio", 100) < 60
            assert stock.get("market_cap", 0) > 5000000000
