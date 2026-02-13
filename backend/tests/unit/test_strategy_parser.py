"""策略解析器测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.engines.strategy_parser import StrategyParser
from app.services.llm_service import LLMService
from app.core.llm_config import LLMSettings


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

    service = LLMService(settings)
    return service


@pytest.fixture
def strategy_parser(llm_service):
    """策略解析器 fixture"""
    return StrategyParser(llm_service)


@pytest.mark.asyncio
async def test_parse_graham_strategy(strategy_parser):
    """测试解析格雷厄姆策略"""
    # Mock LLM response
    mock_response = {
        "conditions": [
            {"field": "pe", "operator": "<", "value": 15, "description": "市盈率小于15"},
            {"field": "pb", "operator": "<", "value": 2, "description": "市净率小于2"},
            {"field": "debt_ratio", "operator": "<", "value": 60, "description": "资产负债率小于60%"}
        ],
        "logic": "AND",
        "confidence": 0.9,
        "summary": "寻找低估值、低负债的价值股"
    }

    strategy_parser.llm_service.structured_output = AsyncMock(return_value=mock_response)

    description = "寻找市盈率小于15、市净率小于2、资产负债率小于60%的价值股"
    result = await strategy_parser.parse(description)

    assert len(result.conditions) == 3
    assert any(c.field == 'pe' and c.operator == '<' and c.value == 15 for c in result.conditions)
    assert any(c.field == 'pb' and c.operator == '<' and c.value == 2 for c in result.conditions)
    assert result.logic == "AND"
    assert len(result.conflicts) == 0
    assert result.confidence == 0.9


@pytest.mark.asyncio
async def test_detect_conflicts(strategy_parser):
    """测试冲突检测"""
    # Mock LLM response with conflicting conditions
    mock_response = {
        "conditions": [
            {"field": "pe", "operator": "<", "value": 10, "description": "市盈率小于10"},
            {"field": "pe", "operator": ">", "value": 20, "description": "市盈率大于20"}
        ],
        "logic": "AND",
        "confidence": 0.7,
        "summary": "冲突的条件"
    }

    strategy_parser.llm_service.structured_output = AsyncMock(return_value=mock_response)

    description = "市盈率小于10且大于20"
    result = await strategy_parser.parse(description)

    assert len(result.conflicts) > 0
    assert any("pe" in conflict for conflict in result.conflicts)


@pytest.mark.asyncio
async def test_validate_invalid_field(strategy_parser):
    """测试无效字段验证"""
    # Mock LLM response with invalid field
    mock_response = {
        "conditions": [
            {"field": "invalid_field", "operator": "<", "value": 10, "description": "无效字段"}
        ],
        "logic": "AND",
        "confidence": 0.5,
        "summary": "无效字段"
    }

    strategy_parser.llm_service.structured_output = AsyncMock(return_value=mock_response)

    description = "无效的策略"

    with pytest.raises(ValueError, match="Invalid field"):
        await strategy_parser.parse(description)
