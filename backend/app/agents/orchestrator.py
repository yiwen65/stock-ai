"""Orchestrator Agent - 主控 Agent"""

from typing import Dict
import asyncio
from app.services.llm_service import LLMService


class OrchestratorAgent:
    """主控 Agent：协调多个专业 Agent"""

    def __init__(
        self,
        llm_service: LLMService,
        data_agent: 'DataAgent',
        fundamental_agent: 'FundamentalAgent',
        technical_agent: 'TechnicalAgent',
        evaluator_agent: 'EvaluatorAgent'
    ):
        self.llm_service = llm_service
        self.data_agent = data_agent
        self.fundamental_agent = fundamental_agent
        self.technical_agent = technical_agent
        self.evaluator_agent = evaluator_agent

    async def analyze_stock(self, stock_code: str) -> Dict:
        """协调多个 Agent 分析股票"""
        # 1. Data Agent 获取数据
        data = await self.data_agent.execute({'stock_code': stock_code})

        # 2. 并行执行分析 Agents
        fundamental_task = self.fundamental_agent.execute(data)
        technical_task = self.technical_agent.execute(data)

        fundamental_result, technical_result = await asyncio.gather(
            fundamental_task,
            technical_task
        )

        # 3. Evaluator Agent 综合评估
        evaluation = await self.evaluator_agent.execute({
            'stock_code': stock_code,
            'fundamental': fundamental_result,
            'technical': technical_result
        })

        return evaluation
