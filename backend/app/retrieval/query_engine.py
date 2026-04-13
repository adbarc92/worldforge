"""
Query engine for semantic search using LlamaIndex and ChromaDB.
"""

from typing import Dict, List, Optional, Any
import chromadb
from llama_index.core import StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.config import settings
from backend.app.database.models import Chunk, Document
from backend.app.llm.provider import get_llm_provider


class QueryEngine:
    """
    Semantic query engine using RAG with LlamaIndex.

    Features:
    - Hybrid search (vector + keyword)
    - Context assembly from top-k chunks
    - Citation generation
    - LLM-based answer generation
    """

    def __init__(self, top_k: int = 5):
        """
        Initialize query engine.

        Args:
            top_k: Number of chunks to retrieve for context
        """
        self.top_k = top_k
        self.llm_provider = get_llm_provider()

        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=settings.chromadb_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="worldforge_chunks",
            metadata={"hnsw:space": "cosine"}
        )

        # Initialize embedding model
        self.embed_model = HuggingFaceEmbedding(
            model_name=settings.embeddings_model,
            cache_folder="/data/models"
        )

        # Configure LlamaIndex settings
        Settings.embed_model = self.embed_model
        Settings.chunk_size = settings.chunk_size
        Settings.chunk_overlap = settings.chunk_overlap

        # Create vector store
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    async def query(
        self,
        query_text: str,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute semantic query and generate answer with citations.

        Args:
            query_text: User's question
            db: Database session
            filters: Optional filters (e.g., document_id, date_range)
            top_k: Override default top_k

        Returns:
            Dict with answer, citations, retrieved_chunks
        """
        k = top_k or self.top_k

        # Step 1: Retrieve relevant chunks
        retrieved_chunks = await self._retrieve_chunks(query_text, k, filters)

        if not retrieved_chunks:
            return {
                "answer": "I couldn't find any relevant information in the knowledge base to answer your question.",
                "citations": [],
                "retrieved_chunks": [],
                "metadata": {
                    "chunks_retrieved": 0,
                    "query": query_text
                }
            }

        # Step 2: Fetch chunk metadata from database
        chunk_metadata = await self._fetch_chunk_metadata(db, retrieved_chunks)

        # Step 3: Assemble context
        context = self._assemble_context(retrieved_chunks, chunk_metadata)

        # Step 4: Generate answer with LLM
        answer = await self._generate_answer(query_text, context)

        # Step 5: Generate citations
        citations = self._generate_citations(chunk_metadata)

        return {
            "answer": answer,
            "citations": citations,
            "retrieved_chunks": [
                {
                    "chunk_id": chunk["id"],
                    "text": chunk["text"][:200] + "...",  # Preview
                    "score": chunk["score"],
                    "document_id": metadata.get("document_id"),
                    "page_number": metadata.get("page_number")
                }
                for chunk, metadata in zip(retrieved_chunks, chunk_metadata)
            ],
            "metadata": {
                "chunks_retrieved": len(retrieved_chunks),
                "query": query_text,
                "top_k": k
            }
        }

    async def _retrieve_chunks(
        self,
        query_text: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using vector similarity search.

        Args:
            query_text: Query string
            top_k: Number of chunks to retrieve
            filters: Optional metadata filters

        Returns:
            List of retrieved chunks with scores
        """
        # Generate query embedding
        query_embedding = self.embed_model.get_text_embedding(query_text)

        # Build where clause for ChromaDB
        where_clause = None
        if filters:
            where_clause = {}
            if "document_id" in filters:
                where_clause["document_id"] = filters["document_id"]

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["metadatas", "documents", "distances"]
        )

        # Format results
        chunks = []
        if results["ids"][0]:  # Check if results exist
            for idx, chunk_id in enumerate(results["ids"][0]):
                chunks.append({
                    "id": chunk_id,
                    "text": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "score": 1 - results["distances"][0][idx]  # Convert distance to similarity
                })

        return chunks

    async def _fetch_chunk_metadata(
        self,
        db: AsyncSession,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fetch additional chunk metadata from database.

        Args:
            db: Database session
            chunks: Retrieved chunks from ChromaDB

        Returns:
            List of metadata dicts
        """
        chunk_ids = [chunk["id"] for chunk in chunks]

        # Query database for chunk details
        result = await db.execute(
            select(Chunk, Document)
            .join(Document, Chunk.document_id == Document.id)
            .where(Chunk.chromadb_id.in_(chunk_ids))
        )
        rows = result.all()

        # Create lookup dict
        metadata_lookup = {}
        for chunk, document in rows:
            metadata_lookup[chunk.chromadb_id] = {
                "document_id": document.id,
                "document_title": document.title,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "file_path": document.file_path
            }

        # Match metadata to chunks in order
        metadata_list = []
        for chunk in chunks:
            metadata = metadata_lookup.get(chunk["id"], {})
            metadata_list.append(metadata)

        return metadata_list

    def _assemble_context(
        self,
        chunks: List[Dict[str, Any]],
        metadata: List[Dict[str, Any]]
    ) -> str:
        """
        Assemble context from retrieved chunks for LLM.

        Args:
            chunks: Retrieved chunks
            metadata: Chunk metadata

        Returns:
            Formatted context string
        """
        context_parts = []

        for idx, (chunk, meta) in enumerate(zip(chunks, metadata), start=1):
            doc_title = meta.get("document_title", "Unknown Document")
            page = meta.get("page_number")
            page_str = f", Page {page}" if page else ""

            context_parts.append(
                f"[Source {idx}: {doc_title}{page_str}]\n{chunk['text']}\n"
            )

        return "\n".join(context_parts)

    async def _generate_answer(self, query: str, context: str) -> str:
        """
        Generate answer using LLM with retrieved context.

        Args:
            query: User's question
            context: Assembled context from chunks

        Returns:
            Generated answer
        """
        prompt = f"""You are an expert assistant helping a worldbuilder understand their fictional universe.

Use the following context from their worldbuilding documents to answer the question. If the context doesn't contain enough information to answer confidently, say so.

When referencing information from the sources, use inline citations in the format [^1], [^2], etc., matching the source numbers in the context.

CONTEXT:
{context}

QUESTION: {query}

ANSWER (with inline citations):"""

        answer = await self.llm_provider.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3  # Lower temperature for factual responses
        )

        return answer.strip()

    def _generate_citations(self, metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate citation list from chunk metadata.

        Args:
            metadata: Chunk metadata

        Returns:
            List of citation dicts
        """
        citations = []

        for idx, meta in enumerate(metadata, start=1):
            citation = {
                "number": idx,
                "document_id": meta.get("document_id"),
                "document_title": meta.get("document_title", "Unknown Document"),
                "page_number": meta.get("page_number"),
                "chunk_index": meta.get("chunk_index")
            }
            citations.append(citation)

        return citations

    async def hybrid_search(
        self,
        query_text: str,
        db: AsyncSession,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Hybrid search combining vector similarity and keyword matching.

        Args:
            query_text: Query string
            db: Database session
            keyword_weight: Weight for keyword matching (0-1)
            vector_weight: Weight for vector similarity (0-1)
            top_k: Number of results

        Returns:
            Query results with hybrid scores
        """
        k = top_k or self.top_k

        # Vector search
        vector_results = await self._retrieve_chunks(query_text, k * 2)  # Get more for reranking

        # Keyword search (simple implementation - can be enhanced)
        keyword_results = await self._keyword_search(query_text, db, k * 2)

        # Combine and rerank
        combined = self._combine_results(
            vector_results,
            keyword_results,
            vector_weight,
            keyword_weight
        )

        # Take top-k
        top_results = combined[:k]

        # Fetch metadata and generate answer
        chunk_metadata = await self._fetch_chunk_metadata(db, top_results)
        context = self._assemble_context(top_results, chunk_metadata)
        answer = await self._generate_answer(query_text, context)
        citations = self._generate_citations(chunk_metadata)

        return {
            "answer": answer,
            "citations": citations,
            "retrieved_chunks": [
                {
                    "chunk_id": chunk["id"],
                    "text": chunk["text"][:200] + "...",
                    "score": chunk["score"]
                }
                for chunk in top_results
            ],
            "metadata": {
                "chunks_retrieved": len(top_results),
                "query": query_text,
                "search_type": "hybrid"
            }
        }

    async def _keyword_search(
        self,
        query_text: str,
        db: AsyncSession,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Simple keyword-based search using database LIKE queries.

        Args:
            query_text: Query string
            db: Database session
            limit: Max results

        Returns:
            List of matching chunks
        """
        # Extract keywords (simple tokenization)
        keywords = query_text.lower().split()

        # Query database for chunks containing keywords
        result = await db.execute(
            select(Chunk)
            .where(Chunk.content.ilike(f"%{keywords[0]}%"))  # Match first keyword
            .limit(limit)
        )
        chunks = result.scalars().all()

        # Format results
        keyword_results = []
        for chunk in chunks:
            # Calculate simple keyword match score
            content_lower = chunk.content.lower()
            matches = sum(1 for kw in keywords if kw in content_lower)
            score = matches / len(keywords) if keywords else 0

            keyword_results.append({
                "id": chunk.chromadb_id,
                "text": chunk.content,
                "score": score,
                "metadata": {"document_id": chunk.document_id}
            })

        return keyword_results

    def _combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        vector_weight: float,
        keyword_weight: float
    ) -> List[Dict[str, Any]]:
        """
        Combine and rerank vector and keyword search results.

        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            vector_weight: Weight for vector scores
            keyword_weight: Weight for keyword scores

        Returns:
            Combined and sorted results
        """
        # Create lookup by chunk ID
        combined_scores = {}

        # Add vector scores
        for result in vector_results:
            chunk_id = result["id"]
            combined_scores[chunk_id] = {
                "chunk": result,
                "vector_score": result["score"],
                "keyword_score": 0.0
            }

        # Add keyword scores
        for result in keyword_results:
            chunk_id = result["id"]
            if chunk_id in combined_scores:
                combined_scores[chunk_id]["keyword_score"] = result["score"]
            else:
                combined_scores[chunk_id] = {
                    "chunk": result,
                    "vector_score": 0.0,
                    "keyword_score": result["score"]
                }

        # Calculate combined scores
        for chunk_id, data in combined_scores.items():
            combined_score = (
                data["vector_score"] * vector_weight +
                data["keyword_score"] * keyword_weight
            )
            data["chunk"]["score"] = combined_score

        # Sort by combined score
        sorted_results = sorted(
            [data["chunk"] for data in combined_scores.values()],
            key=lambda x: x["score"],
            reverse=True
        )

        return sorted_results
