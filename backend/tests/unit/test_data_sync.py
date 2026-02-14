# backend/tests/unit/test_data_sync.py

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, time
from app.tasks.data_sync import (
    is_trading_time,
    sync_realtime_quotes,
    sync_kline_data,
    sync_financial_data,
    sync_all_stocks_data,
    _sync_realtime_quotes,
    _sync_kline_data,
    _sync_financial_data,
    _sync_all_stocks_data
)


class TestTradingTime:
    """测试交易时间判断"""

    @patch('app.tasks.data_sync.datetime')
    def test_is_trading_time_morning(self, mock_datetime):
        """测试早盘交易时间"""
        mock_now = Mock()
        mock_now.weekday.return_value = 1  # Tuesday
        mock_now.time.return_value = time(10, 0)  # 10:00
        mock_datetime.now.return_value = mock_now

        assert is_trading_time() is True

    @patch('app.tasks.data_sync.datetime')
    def test_is_trading_time_afternoon(self, mock_datetime):
        """测试午盘交易时间"""
        mock_now = Mock()
        mock_now.weekday.return_value = 3  # Thursday
        mock_now.time.return_value = time(14, 30)  # 14:30
        mock_datetime.now.return_value = mock_now

        assert is_trading_time() is True

    @patch('app.tasks.data_sync.datetime')
    def test_is_not_trading_time_weekend(self, mock_datetime):
        """测试周末非交易时间"""
        mock_now = Mock()
        mock_now.weekday.return_value = 5  # Saturday
        mock_now.time.return_value = time(10, 0)
        mock_datetime.now.return_value = mock_now

        assert is_trading_time() is False

    @patch('app.tasks.data_sync.datetime')
    def test_is_not_trading_time_lunch(self, mock_datetime):
        """测试午休非交易时间"""
        mock_now = Mock()
        mock_now.weekday.return_value = 2  # Wednesday
        mock_now.time.return_value = time(12, 0)  # 12:00
        mock_datetime.now.return_value = mock_now

        assert is_trading_time() is False

    @patch('app.tasks.data_sync.datetime')
    def test_is_not_trading_time_after_close(self, mock_datetime):
        """测试收盘后非交易时间"""
        mock_now = Mock()
        mock_now.weekday.return_value = 4  # Friday
        mock_now.time.return_value = time(16, 0)  # 16:00
        mock_datetime.now.return_value = mock_now

        assert is_trading_time() is False


class TestRealtimeQuotesSync:
    """测试实时行情同步"""

    @pytest.mark.asyncio
    @patch('app.tasks.data_sync.DataService')
    @patch('app.tasks.data_sync.get_redis')
    @patch('app.tasks.data_sync.get_influxdb')
    async def test_sync_realtime_quotes_success(
        self, mock_influxdb, mock_redis, mock_data_service
    ):
        """测试成功同步实时行情"""
        # Mock data service
        mock_service = Mock()
        mock_service.get_all_stock_codes = AsyncMock(return_value=['000001', '000002'])
        mock_service.fetch_realtime_quotes_batch = AsyncMock(return_value=[
            {'stock_code': '000001', 'price': 10.5},
            {'stock_code': '000002', 'price': 20.3}
        ])
        mock_data_service.return_value = mock_service

        # Mock Redis
        mock_redis_client = Mock()
        mock_redis_client.setex = AsyncMock()
        mock_redis.return_value = mock_redis_client

        # Mock InfluxDB
        mock_influx_client = Mock()
        mock_influx_client.write_realtime_quotes = AsyncMock()
        mock_influxdb.return_value = mock_influx_client

        # Execute
        result = await _sync_realtime_quotes()

        # Verify
        assert result == 2
        assert mock_redis_client.setex.call_count == 2
        mock_influx_client.write_realtime_quotes.assert_called_once()

    @patch('app.tasks.data_sync.is_trading_time')
    @patch('app.tasks.data_sync.asyncio.run')
    def test_sync_realtime_quotes_not_trading_time(
        self, mock_asyncio_run, mock_is_trading_time
    ):
        """测试非交易时间不同步"""
        mock_is_trading_time.return_value = False

        result = sync_realtime_quotes()

        assert result == "Not trading time"
        mock_asyncio_run.assert_not_called()


class TestKlineDataSync:
    """测试 K 线数据同步"""

    @pytest.mark.asyncio
    @patch('app.tasks.data_sync.DataService')
    @patch('app.tasks.data_sync.get_influxdb')
    async def test_sync_kline_data_success(self, mock_influxdb, mock_data_service):
        """测试成功同步 K 线数据"""
        # Mock data service
        mock_service = Mock()
        mock_kline_data = [
            {'date': '2024-01-01', 'open': 10.0, 'close': 10.5},
            {'date': '2024-01-02', 'open': 10.5, 'close': 11.0}
        ]
        mock_service.fetch_kline_data = AsyncMock(return_value=mock_kline_data)
        mock_data_service.return_value = mock_service

        # Mock InfluxDB
        mock_influx_client = Mock()
        mock_influx_client.write_kline_data = AsyncMock()
        mock_influxdb.return_value = mock_influx_client

        # Execute
        result = await _sync_kline_data('000001', '1d')

        # Verify
        assert result == 2
        mock_service.fetch_kline_data.assert_called_once_with(
            '000001', period='1d', days=500
        )
        mock_influx_client.write_kline_data.assert_called_once_with(
            '000001', '1d', mock_kline_data
        )


class TestFinancialDataSync:
    """测试财务数据同步"""

    @pytest.mark.asyncio
    @patch('app.tasks.data_sync.DataService')
    @patch('app.tasks.data_sync.get_db')
    @patch('app.tasks.data_sync.StockFinancial')
    async def test_sync_financial_data_success(
        self, mock_stock_financial, mock_get_db, mock_data_service
    ):
        """测试成功同步财务数据"""
        # Mock data service
        mock_service = Mock()
        mock_financials = [
            {'stock_code': '000001', 'year': 2023, 'revenue': 1000000},
            {'stock_code': '000001', 'year': 2024, 'revenue': 1200000}
        ]
        mock_service.fetch_financial_data = AsyncMock(return_value=mock_financials)
        mock_data_service.return_value = mock_service

        # Mock database
        mock_db = Mock()
        mock_db.merge = Mock()
        mock_db.commit = Mock()
        mock_db.close = Mock()
        mock_get_db.return_value = iter([mock_db])

        # Execute
        result = await _sync_financial_data('000001')

        # Verify
        assert result == 2
        assert mock_db.merge.call_count == 2
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()


class TestBatchSync:
    """测试批量同步"""

    @pytest.mark.asyncio
    @patch('app.tasks.data_sync.DataService')
    @patch('app.tasks.data_sync.group')
    async def test_sync_all_stocks_data(self, mock_group, mock_data_service):
        """测试批量同步所有股票数据"""
        # Mock data service
        mock_service = Mock()
        mock_service.get_all_stock_codes = AsyncMock(
            return_value=['000001', '000002', '000003']
        )
        mock_data_service.return_value = mock_service

        # Mock Celery group
        mock_job = Mock()
        mock_job.apply_async = Mock()
        mock_group.return_value = mock_job

        # Execute
        result = await _sync_all_stocks_data()

        # Verify
        assert result == "Syncing 3 stocks"
        mock_group.assert_called_once()
        mock_job.apply_async.assert_called_once()
