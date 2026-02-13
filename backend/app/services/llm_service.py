"""LLM 服务模块"""

from openai import AsyncOpenAI
from typing import List, Dict, Optional
import json

from app.core.llm_config import LLMSettings


class LLMService:
    """LLM 服务"""

    def __init__(self, settings: LLMSettings):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """调用 LLM 生成回复"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens
        )
        return response.choices[0].message.content

    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        response_format: Dict
    ) -> Dict:
        """调用 LLM 生成结构化输出（JSON）"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3  # 降低温度以提高结构化输出准确性
        )
        return json.loads(response.choices[0].message.content)
