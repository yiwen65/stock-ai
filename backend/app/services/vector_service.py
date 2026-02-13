"""向量检索服务模块"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional
from app.services.embedding_service import EmbeddingService


class VectorService:
    """向量检索服务"""

    def __init__(self, host: str = "localhost", port: int = 6333, openai_api_key: str = ""):
        self.client = QdrantClient(host=host, port=port)
        self.embedding_service = EmbeddingService(openai_api_key)

    async def create_collection(self, collection_name: str, vector_size: int = 1536):
        """创建向量集合"""
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )

    async def add_documents(
        self,
        collection_name: str,
        documents: List[Dict]
    ):
        """添加文档到向量库"""
        # 生成向量
        texts = [doc['content'] for doc in documents]
        vectors = await self.embedding_service.embed_batch(texts)

        # 构建 Points
        points = [
            PointStruct(
                id=i,
                vector=vector,
                payload=doc
            )
            for i, (vector, doc) in enumerate(zip(vectors, documents))
        ]

        # 插入向量库
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    async def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """语义搜索"""
        # 生成查询向量
        query_vector = await self.embedding_service.embed_text(query)

        # 向量检索
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filters
        )

        return [
            {
                'score': result.score,
                'payload': result.payload
            }
            for result in results
        ]
