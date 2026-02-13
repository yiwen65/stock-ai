"""LLM 服务测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.llm_service import LLMService
from app.core.llm_config import LLMSettings


@pytest.fixture
def llm_settings():
    """LLM 配置 fixture"""
    return LLMSettings(
        OPENAI_API_KEY="test-key",
        OPENAI_MODEL="gpt-4-turbo-preview",
        OPENAI_TEMPERATURE=0.7,
        OPENAI_MAX_TOKENS=2000
    )


@pytest.fixture
def llm_service(llm_settings, monkeypatch):
    """LLM 服务 fixture"""
    # Mock AsyncOpenAI
    mock_client = MagicMock()
    monkeypatch.setattr("app.services.llm_service.AsyncOpenAI", lambda **kwargs: mock_client)
    return LLMService(llm_settings)


@pytest.mark.asyncio
async def test_llm_chat_completion(llm_service):
    """测试聊天补全"""
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello, world!"

    llm_service.client.chat.completions.create = AsyncMock(return_value=mock_response)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello"}
    ]

    response = await llm_service.chat_completion(messages)

    assert isinstance(response, str)
    assert response == "Hello, world!"
    llm_service.client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_llm_structured_output(llm_service):
    """测试结构化输出"""
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"result": "success"}'

    llm_service.client.chat.completions.create = AsyncMock(return_value=mock_response)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Return JSON"}
    ]

    response = await llm_service.structured_output(messages, {"type": "json_object"})

    assert isinstance(response, dict)
    assert response["result"] == "success"
    llm_service.client.chat.completions.create.assert_called_once()
