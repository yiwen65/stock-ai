"""Orchestrator Agent - 主控 Agent"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from app.services.llm_service import LLMService
from app.agents.data_agent import DataAgent
from app.agents.fundamental_agent import FundamentalAgent
from app.agents.technical_agent import TechnicalAgent
from app.agents.capital_flow_agent import CapitalFlowAgent
from app.agents.news_agent import NewsAgent
from app.agents.evaluator_agent import EvaluatorAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """主控 Agent：协调 DataAgent → 4 个分析 Agent 并行 → EvaluatorAgent"""

    def __init__(
        self,
        llm_service: LLMService,
        data_agent: Optional[DataAgent] = None,
        fundamental_agent: Optional[FundamentalAgent] = None,
        technical_agent: Optional[TechnicalAgent] = None,
        capital_flow_agent: Optional[CapitalFlowAgent] = None,
        news_agent: Optional[NewsAgent] = None,
        evaluator_agent: Optional[EvaluatorAgent] = None,
    ):
        self.llm_service = llm_service
        self.data_agent = data_agent or DataAgent(llm_service)
        self.fundamental_agent = fundamental_agent or FundamentalAgent(llm_service)
        self.technical_agent = technical_agent or TechnicalAgent(llm_service)
        self.capital_flow_agent = capital_flow_agent or CapitalFlowAgent(llm_service)
        self.news_agent = news_agent or NewsAgent(llm_service)
        self.evaluator_agent = evaluator_agent or EvaluatorAgent(llm_service)

    async def analyze_stock(self, stock_code: str) -> Dict[str, Any]:
        """协调多个 Agent 分析股票

        Flow: DataAgent → (FundamentalAgent | TechnicalAgent | CapitalFlowAgent | NewsAgent) → EvaluatorAgent
        """
        t0 = time.time()
        logger.info(f"[Orchestrator] Start analysis for {stock_code}")

        # 1. DataAgent: fetch all raw data
        data = await self.data_agent.execute({"stock_code": stock_code})
        logger.info(f"[Orchestrator] Data fetched in {time.time() - t0:.1f}s")

        # 2. Four analysis agents in parallel
        t1 = time.time()
        fundamental_task = self.fundamental_agent.execute(data)
        technical_task = self.technical_agent.execute(data)
        capital_flow_task = self.capital_flow_agent.execute(data)
        news_task = self.news_agent.execute(data)

        fundamental_result, technical_result, capital_result, news_result = await asyncio.gather(
            fundamental_task, technical_task, capital_flow_task, news_task,
            return_exceptions=True,
        )

        # Handle exceptions gracefully
        if isinstance(fundamental_result, Exception):
            logger.error(f"FundamentalAgent failed: {fundamental_result}")
            fundamental_result = {"agent": "fundamental", "score": 5.0, "summary": "分析失败"}
        if isinstance(technical_result, Exception):
            logger.error(f"TechnicalAgent failed: {technical_result}")
            technical_result = {"agent": "technical", "score": 5.0, "trend": "震荡", "summary": "分析失败"}
        if isinstance(capital_result, Exception):
            logger.error(f"CapitalFlowAgent failed: {capital_result}")
            capital_result = {"agent": "capital_flow", "score": 5.0, "trend": "无明显趋势", "summary": "分析失败"}
        if isinstance(news_result, Exception):
            logger.error(f"NewsAgent failed: {news_result}")
            news_result = {"agent": "news", "score": 5.0, "sentiment": "中性", "summary": "分析失败"}

        logger.info(f"[Orchestrator] 4 agents completed in {time.time() - t1:.1f}s")

        # 3. EvaluatorAgent: comprehensive evaluation
        t2 = time.time()
        evaluation = await self.evaluator_agent.execute({
            "stock_code": stock_code,
            "stock_name": data.get("stock_name", stock_code),
            "realtime": data.get("realtime", {}),
            "fundamental": fundamental_result,
            "technical": technical_result,
            "capital_flow": capital_result,
            "news": news_result,
        })
        logger.info(f"[Orchestrator] Evaluator completed in {time.time() - t2:.1f}s")

        total = time.time() - t0
        logger.info(f"[Orchestrator] Total analysis time: {total:.1f}s")

        evaluation["analysis_time"] = round(total, 2)
        evaluation["news"] = news_result
        return evaluation
