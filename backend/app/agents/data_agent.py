"""Data Agent - 数据获取 Agent"""

from typing import Dict, Any
import asyncio
import logging
from app.agents.base_agent import BaseAgent
from app.services.data_service import DataService

logger = logging.getLogger(__name__)


class DataAgent(BaseAgent):
    """数据获取 Agent — 并行拉取行情/K线/财务/资金数据"""

    def __init__(self, llm_service=None, name: str = "data-agent"):
        super().__init__(llm_service, name)
        self.data_service = DataService()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """并行获取股票所有维度的数据"""
        stock_code = context['stock_code']

        realtime_task = self.data_service.fetch_realtime_quote(stock_code)
        kline_task = self.data_service.fetch_kline_data(stock_code, period='1d', days=500)
        financial_task = self.data_service.fetch_financial_data(stock_code)
        capital_task = self.data_service.fetch_capital_flow(stock_code)
        news_task = self.data_service.fetch_stock_news(stock_code, limit=10)

        realtime, kline, financial, capital_flow, news = await asyncio.gather(
            realtime_task, kline_task, financial_task, capital_task, news_task,
            return_exceptions=True,
        )

        def _safe(val):
            if isinstance(val, Exception):
                logger.warning(f"DataAgent fetch error for {stock_code}: {val}")
                return None
            return val

        return {
            'stock_code': stock_code,
            'stock_name': (_safe(realtime) or {}).get('stock_name', stock_code),
            'realtime': _safe(realtime) or {},
            'kline': _safe(kline) or [],
            'financial': _safe(financial) or [],
            'capital_flow': _safe(capital_flow) or {},
            'news': _safe(news) or [],
        }

    def _get_system_prompt(self) -> str:
        return "你是数据获取代理，负责收集股票的行情、K线、财务和资金流向数据。"
