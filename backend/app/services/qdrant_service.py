"""
Qdrant vector database service for semantic search
"""
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from loguru import logger

from app.core.config import settings


class QdrantService:
    """Service for interacting with Qdrant vector database"""

    def __init__(self):
        """Initialize Qdrant client"""
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "canon_documents"
        self.embedding_size = 1024  # BGE-large-en-v1.5 dimension

    async def ensure_collection(self):
        """Ensure the collection exists, create if not"""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_size,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")
            raise

    async def add_vectors(
        self,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: List[str]
    ):
        """
        Add vectors to Qdrant

        Args:
            vectors: List of embedding vectors
            payloads: List of metadata dictionaries
            ids: List of unique identifiers
        """
        try:
            points = [
                PointStruct(id=id, vector=vector, payload=payload)
                for id, vector, payload in zip(ids, vectors, payloads)
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"Added {len(points)} vectors to Qdrant")
        except Exception as e:
            logger.error(f"Error adding vectors to Qdrant: {e}")
            raise

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional filter conditions

        Returns:
            List of search results with scores and payloads
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filter_dict
            )

            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            raise

    async def delete_by_document_id(self, document_id: str):
        """Delete all vectors for a document"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {
                                "key": "document_id",
                                "match": {"value": document_id}
                            }
                        ]
                    }
                }
            )
            logger.info(f"Deleted vectors for document: {document_id}")
        except Exception as e:
            logger.error(f"Error deleting from Qdrant: {e}")
            raise
