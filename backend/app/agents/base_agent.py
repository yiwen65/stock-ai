"""Agent 基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from app.services.llm_service import LLMService


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, llm_service: LLMService, name: str):
        self.llm_service = llm_service
        self.name = name

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent 任务"""
        pass

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """构建提示词"""
        pass

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        return await self.llm_service.chat_completion(messages)

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass
