# backend/tests/unit/test_stock_filter.py
import pytest
from app.engines.stock_filter import StockFilter
from app.schemas.strategy import FilterCondition, ConditionOperator

@pytest.mark.asyncio
async def test_filter_by_pe():
    filter_engine = StockFilter()
    condition = FilterCondition(field="pe", operator=ConditionOperator.LT, value=15.0)

    stocks = await filter_engine.apply_filter([condition])

    assert isinstance(stocks, list)
    assert all(stock.get("pe", 999) < 15.0 for stock in stocks if stock.get("pe"))

@pytest.mark.asyncio
async def test_filter_multiple_conditions():
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
