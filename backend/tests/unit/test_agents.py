"""Agent 测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.base_agent import BaseAgent
from app.agents.orchestrator import OrchestratorAgent
from app.services.llm_service import LLMService
from app.core.llm_config import LLMSettings


class MockAgent(BaseAgent):
    """测试用 Agent"""

    async def execute(self, context):
        return {"result": "test"}

    def _get_system_prompt(self):
        return "Test system prompt"


@pytest.fixture
def llm_service(monkeypatch):
    """LLM 服务 fixture"""
    settings = LLMSettings(
        OPENAI_API_KEY="test-key",
        OPENAI_MODEL="gpt-4-turbo-preview"
    )

    # Mock AsyncOpenAI to avoid actual client initialization
    mock_client = MagicMock()
    monkeypatch.setattr("app.services.llm_service.AsyncOpenAI", lambda **kwargs: mock_client)

    return LLMService(settings)


@pytest.mark.asyncio
async def test_base_agent(llm_service):
    """测试基础 Agent"""
    agent = MockAgent(llm_service, "test-agent")
    assert agent.name == "test-agent"
    result = await agent.execute({})
    assert result["result"] == "test"


@pytest.mark.asyncio
async def test_orchestrator_agent(llm_service):
    """测试 Orchestrator Agent"""
    # Mock agents
    data_agent = MagicMock()
    data_agent.execute = AsyncMock(return_value={
        "stock_code": "600519",
        "realtime": {},
        "kline": {},
        "financial": {}
    })

    fundamental_agent = MagicMock()
    fundamental_agent.execute = AsyncMock(return_value={
        "agent": "fundamental",
        "analysis": "基本面分析结果",
        "score": 8.5
    })

    technical_agent = MagicMock()
    technical_agent.execute = AsyncMock(return_value={
        "agent": "technical",
        "analysis": "技术面分析结果",
        "score": 7.5
    })

    evaluator_agent = MagicMock()
    evaluator_agent.execute = AsyncMock(return_value={
        "overall_score": 8.0,
        "risk_level": "中",
        "recommendation": "买入",
        "summary": "综合评估结果"
    })

    orchestrator = OrchestratorAgent(
        llm_service=llm_service,
        data_agent=data_agent,
        fundamental_agent=fundamental_agent,
        technical_agent=technical_agent,
        evaluator_agent=evaluator_agent
    )

    result = await orchestrator.analyze_stock("600519")

    assert result["overall_score"] == 8.0
    assert result["recommendation"] == "买入"
    data_agent.execute.assert_called_once()
    fundamental_agent.execute.assert_called_once()
    technical_agent.execute.assert_called_once()
    evaluator_agent.execute.assert_called_once()
