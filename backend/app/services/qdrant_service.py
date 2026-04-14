"""Qdrant vector database service for semantic search (async)."""

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.core.config import settings


class QdrantService:
    """Async service for interacting with Qdrant vector database."""

    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "canon_documents"

    async def ensure_collection(self):
        """Ensure the collection exists, create if not."""
        collections = await self.client.get_collections()
        names = [c.name for c in collections.collections]
        if self.collection_name not in names:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE,
                ),
            )

    async def upsert(
        self, ids: list[str], vectors: list[list[float]], payloads: list[dict]
    ):
        """Upsert vectors with payloads into the collection."""
        points = [
            PointStruct(id=id_, vector=vec, payload=payload)
            for id_, vec, payload in zip(ids, vectors, payloads)
        ]
        await self.client.upsert(collection_name=self.collection_name, points=points)

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """Search for similar vectors, optionally filtered by payload fields."""
        qdrant_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            qdrant_filter = Filter(must=conditions)

        results = await self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [
            {"id": point.id, "score": point.score, "payload": point.payload}
            for point in results.points
        ]

    async def search_by_filter(self, filters: dict, limit: int = 100) -> list[dict]:
        """Retrieve points matching a filter (no vector query).

        Returns up to `limit` results from a single scroll page. Does not paginate.
        Returns flattened dicts with id, text, document_id, title, project_id.
        """
        must = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filters.items()
        ]
        query_filter = Filter(must=must)
        points, _ = await self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=query_filter,
            limit=limit,
            with_vectors=False,
            with_payload=True,
        )
        return [
            {
                "id": str(p.id),
                "text": p.payload.get("text", ""),
                "document_id": p.payload.get("document_id", ""),
                "title": p.payload.get("title", ""),
                "project_id": p.payload.get("project_id", ""),
            }
            for p in points
        ]

    async def delete_by_document(self, document_id: str):
        """Delete all vectors associated with a given document_id."""
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=document_id)
                    )
                ]
            ),
        )

    async def delete_by_project(self, project_id: str):
        """Delete all vectors associated with a given project_id."""
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="project_id", match=MatchValue(value=project_id)
                    )
                ]
            ),
        )

    async def close(self):
        """Close the underlying client connection."""
        await self.client.close()
