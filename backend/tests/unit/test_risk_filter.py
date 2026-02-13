# backend/tests/unit/test_risk_filter.py
import pytest
from app.engines.risk_filter import RiskFilter

@pytest.fixture
def risk_filter():
    return RiskFilter()

@pytest.fixture
def sample_stocks():
    return [
        {
            "stock_code": "600000",
            "stock_name": "浦发银行",
            "market_cap": 5000000000,
            "volume": 10000000,
            "status": "normal"
        },
        {
            "stock_code": "600001",
            "stock_name": "*ST华信",
            "market_cap": 2000000000,
            "volume": 5000000,
            "status": "normal"
        },
        {
            "stock_code": "600002",
            "stock_name": "ST东电",
            "market_cap": 1500000000,
            "volume": 3000000,
            "status": "normal"
        },
        {
            "stock_code": "600003",
            "stock_name": "小盘股",
            "market_cap": 500000000,
            "volume": 2000000,
            "status": "normal"
        },
        {
            "stock_code": "600004",
            "stock_name": "停牌股",
            "market_cap": 3000000000,
            "volume": 0,
            "status": "suspended"
        },
        {
            "stock_code": "600005",
            "stock_name": "低流动性",
            "market_cap": 2000000000,
            "volume": 500000,
            "status": "normal"
        }
    ]

@pytest.mark.asyncio
async def test_filter_st_stocks(risk_filter, sample_stocks):
    """Test ST stock filtering"""
    import pandas as pd
    df = pd.DataFrame(sample_stocks)

    result_df = risk_filter._filter_st_stocks(df)

    # Should remove *ST华信 and ST东电
    assert len(result_df) == 4
    assert "*ST华信" not in result_df["stock_name"].values
    assert "ST东电" not in result_df["stock_name"].values

@pytest.mark.asyncio
async def test_filter_suspended_stocks(risk_filter, sample_stocks):
    """Test suspended stock filtering"""
    import pandas as pd
    df = pd.DataFrame(sample_stocks)

    result_df = risk_filter._filter_suspended_stocks(df)

    # Should remove 停牌股 (status=suspended and volume=0)
    assert len(result_df) == 5
    assert "停牌股" not in result_df["stock_name"].values

@pytest.mark.asyncio
async def test_filter_low_liquidity(risk_filter, sample_stocks):
    """Test low liquidity filtering"""
    import pandas as pd
    df = pd.DataFrame(sample_stocks)

    result_df = risk_filter._filter_low_liquidity(df)

    # Should remove stocks with volume < 1,000,000 (低流动性 and 停牌股)
    assert len(result_df) == 4
    assert "低流动性" not in result_df["stock_name"].values
    assert "停牌股" not in result_df["stock_name"].values

@pytest.mark.asyncio
async def test_filter_small_cap(risk_filter, sample_stocks):
    """Test small cap filtering"""
    import pandas as pd
    df = pd.DataFrame(sample_stocks)

    result_df = risk_filter._filter_small_cap(df)

    # Should remove stocks with market_cap < 1,000,000,000
    assert len(result_df) == 5
    assert "小盘股" not in result_df["stock_name"].values

@pytest.mark.asyncio
async def test_apply_all_filters(risk_filter, sample_stocks):
    """Test applying all filters together"""
    result = await risk_filter.apply_all_filters(sample_stocks)

    # Should only keep 浦发银行 (passes all filters)
    assert len(result) == 1
    assert result[0]["stock_name"] == "浦发银行"

@pytest.mark.asyncio
async def test_apply_all_filters_empty_list(risk_filter):
    """Test applying filters to empty list"""
    result = await risk_filter.apply_all_filters([])
    assert result == []

@pytest.mark.asyncio
async def test_set_min_market_cap(risk_filter, sample_stocks):
    """Test setting custom minimum market cap"""
    risk_filter.set_min_market_cap(3000000000)

    result = await risk_filter.apply_all_filters(sample_stocks)

    # Only 浦发银行 has market_cap >= 3B and passes other filters
    assert len(result) == 1
    assert result[0]["stock_name"] == "浦发银行"

@pytest.mark.asyncio
async def test_set_min_volume(risk_filter, sample_stocks):
    """Test setting custom minimum volume"""
    risk_filter.set_min_volume(8000000)

    result = await risk_filter.apply_all_filters(sample_stocks)

    # Only 浦发银行 has volume >= 8M and passes other filters
    assert len(result) == 1
    assert result[0]["stock_name"] == "浦发银行"
