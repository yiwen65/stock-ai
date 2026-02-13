"""Embedding 服务模块"""

from openai import AsyncOpenAI
from typing import List


class EmbeddingService:
    """文本向量化服务"""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"

    async def embed_text(self, text: str) -> List[float]:
        """生成文本向量"""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成向量"""
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
