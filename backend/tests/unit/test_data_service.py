# backend/tests/unit/test_data_service.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.data_service import DataService

@pytest.mark.asyncio
@patch('app.services.data_service.ak.stock_info_a_code_name')
async def test_fetch_stock_list(mock_ak):
    """Test fetching stock list with mocked data"""
    # Mock AKShare response
    import pandas as pd
    mock_df = pd.DataFrame({
        'code': ['600000', '600036', '000001'],
        'name': ['浦发银行', '招商银行', '平安银行']
    })
    mock_ak.return_value = mock_df

    service = DataService()
    stocks = await service.fetch_stock_list()

    assert isinstance(stocks, list)
    assert len(stocks) == 3
    assert "stock_code" in stocks[0]
    assert "stock_name" in stocks[0]
    assert stocks[0]["stock_code"] == "600000"
    assert stocks[0]["stock_name"] == "浦发银行"

@pytest.mark.asyncio
@patch('app.services.data_service.ak.stock_zh_a_spot_em')
async def test_fetch_realtime_quote(mock_ak):
    """Test fetching realtime quote with mocked data"""
    # Mock AKShare response
    import pandas as pd
    mock_df = pd.DataFrame({
        '代码': ['600519'],
        '最新价': [1800.0],
        '涨跌额': [20.0],
        '涨跌幅': [1.12],
        '成交量': [1000000],
        '成交额': [1800000000.0],
        '最高': [1820.0],
        '最低': [1780.0],
        '今开': [1790.0],
        '昨收': [1780.0]
    })
    mock_ak.return_value = mock_df

    service = DataService()
    quote = await service.fetch_realtime_quote("600519")

    assert quote is not None
    assert "price" in quote
    assert "pct_change" in quote
    assert quote["stock_code"] == "600519"
    assert quote["price"] == 1800.0
    assert quote["pct_change"] == 1.12
