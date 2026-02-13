"""Data Agent - 数据获取 Agent"""

from typing import Dict
import asyncio
from app.agents.base_agent import BaseAgent
from app.services.data_service import DataService


class DataAgent(BaseAgent):
    """数据获取 Agent"""

    def __init__(self, llm_service, name: str = "data-agent"):
        super().__init__(llm_service, name)
        self.data_service = DataService()

    async def execute(self, context: Dict) -> Dict:
        """执行数据获取任务"""
        stock_code = context['stock_code']

        # 并行获取数据
        realtime_task = self._get_realtime_data(stock_code)
        kline_task = self._get_kline_data(stock_code)
        financial_task = self._get_financial_data(stock_code)

        realtime, kline, financial = await asyncio.gather(
            realtime_task, kline_task, financial_task
        )

        return {
            'stock_code': stock_code,
            'realtime': realtime,
            'kline': kline,
            'financial': financial
        }

    async def _get_realtime_data(self, stock_code: str) -> Dict:
        """获取实时行情数据"""
        try:
            return await self.data_service.get_realtime_quote(stock_code)
        except Exception as e:
            return {"error": str(e)}

    async def _get_kline_data(self, stock_code: str) -> Dict:
        """获取K线数据"""
        try:
            return await self.data_service.get_kline(stock_code, period="daily", adjust="qfq")
        except Exception as e:
            return {"error": str(e)}

    async def _get_financial_data(self, stock_code: str) -> Dict:
        """获取财务数据"""
        try:
            return await self.data_service.get_financial_data(stock_code)
        except Exception as e:
            return {"error": str(e)}

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return "数据获取 Agent"
