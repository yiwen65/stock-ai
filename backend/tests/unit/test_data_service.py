# backend/tests/unit/test_data_service.py
import pytest
from app.services.data_service import DataService

@pytest.mark.asyncio
async def test_fetch_stock_list():
    service = DataService()
    stocks = await service.fetch_stock_list()
    assert isinstance(stocks, list)
    assert len(stocks) > 0
    assert "stock_code" in stocks[0]
    assert "stock_name" in stocks[0]

@pytest.mark.asyncio
async def test_fetch_realtime_quote():
    service = DataService()
    quote = await service.fetch_realtime_quote("600519")
    assert quote is not None
    assert "price" in quote
    assert "pct_change" in quote
