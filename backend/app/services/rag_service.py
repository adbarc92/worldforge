"""
RAG (Retrieval Augmented Generation) service
Handles query processing, context retrieval, and answer generation
"""
from typing import List, Dict, Any, Tuple
from loguru import logger

from app.core.config import settings
from app.services.ollama_service import OllamaService
from app.services.qdrant_service import QdrantService
from app.services.neo4j_service import Neo4jService


class RAGService:
    """Service for RAG query processing"""

    def __init__(self):
        """Initialize RAG service"""
        self.ollama_service = OllamaService()
        self.qdrant_service = QdrantService()
        self.neo4j_service = Neo4jService()

    async def query(
        self,
        question: str,
        top_k: int = 10,
        include_proposed: bool = False
    ) -> Dict[str, Any]:
        """
        Process a natural language query using RAG

        Steps:
        1. Embed the question
        2. Retrieve relevant chunks (hybrid search)
        3. Optionally get related entities from graph
        4. Assemble context
        5. Generate answer with LLM
        6. Add citations

        Args:
            question: Natural language question
            top_k: Number of results to retrieve
            include_proposed: Include proposed (non-canonical) content

        Returns:
            Dictionary with answer and citations
        """
        logger.info(f"Processing query: {question}")

        try:
            # Step 1: Embed question
            query_embedding = await self.ollama_service.embed(question)

            # Step 2: Retrieve relevant chunks
            results = await self._hybrid_search(
                query_embedding=query_embedding,
                query_text=question,
                top_k=top_k,
                include_proposed=include_proposed
            )

            # Step 3: Assemble context
            context, citations = await self._assemble_context(results)

            # Step 4: Generate answer
            answer = await self._generate_answer(question, context)

            return {
                "answer": answer,
                "citations": citations,
                "context_length": len(context)
            }

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise

    async def _hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        top_k: int,
        include_proposed: bool
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword search

        Args:
            query_embedding: Query embedding vector
            query_text: Original query text
            top_k: Number of results
            include_proposed: Include proposed content

        Returns:
            List of search results
        """
        try:
            # Build filter for canon status
            filter_dict = None
            if not include_proposed:
                filter_dict = {
                    "must": [
                        {
                            "key": "canon_status",
                            "match": {"value": "canonical"}
                        }
                    ]
                }

            # Semantic search via Qdrant
            results = await self.qdrant_service.search(
                query_vector=query_embedding,
                top_k=top_k,
                filter_dict=filter_dict
            )

            # TODO: Add keyword search (BM25) and merge results
            # TODO: Add graph-based retrieval for related entities

            return results

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            raise

    async def _assemble_context(
        self,
        search_results: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Assemble context from search results

        Args:
            search_results: List of search results

        Returns:
            Tuple of (context_text, citations)
        """
        try:
            context_parts = []
            citations = []

            for i, result in enumerate(search_results):
                payload = result.get("payload", {})
                text = payload.get("text", "")
                score = result.get("score", 0.0)

                # Add to context
                context_parts.append(f"[Source {i+1}]\n{text}\n")

                # Add citation
                citations.append({
                    "document_id": payload.get("document_id"),
                    "document_title": payload.get("title"),
                    "chunk_text": text[:200] + "...",  # Truncate for display
                    "relevance_score": score
                })

            # Combine context, respecting token limits
            context = "\n".join(context_parts)

            # Truncate if too long
            max_chars = settings.CONTEXT_MAX_TOKENS * 4  # Rough estimate
            if len(context) > max_chars:
                context = context[:max_chars] + "\n[Context truncated...]"

            return context, citations

        except Exception as e:
            logger.error(f"Error assembling context: {e}")
            raise

    async def _generate_answer(
        self,
        question: str,
        context: str
    ) -> str:
        """
        Generate answer using LLM with retrieved context

        Args:
            question: User question
            context: Retrieved context

        Returns:
            Generated answer
        """
        try:
            system_prompt = """You are an assistant for Canon Builder, a knowledge system for worldbuilding.
Your task is to answer questions based STRICTLY on the provided canonical sources.

Rules:
1. Only use information from the provided sources
2. If the sources don't contain enough information, say so
3. Be concise and accurate
4. Reference source numbers when making claims [Source N]
5. Never make up information or speculate beyond the sources"""

            user_prompt = f"""Based on the following canonical sources, answer this question:

Question: {question}

Sources:
{context}

Answer:"""

            answer = await self.ollama_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3  # Lower temperature for factual answers
            )

            return answer.strip()

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise

    async def generate_extension(
        self,
        prompt: str,
        creativity_level: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate an extension proposal

        Args:
            prompt: Extension prompt
            creativity_level: LLM temperature (0-1)

        Returns:
            Generated proposal with metadata
        """
        logger.info(f"Generating extension: {prompt[:100]}...")

        try:
            # Step 1: Retrieve relevant canonical context
            query_embedding = await self.ollama_service.embed(prompt)
            results = await self._hybrid_search(
                query_embedding=query_embedding,
                query_text=prompt,
                top_k=10,
                include_proposed=False  # Only use canonical
            )

            context, sources = await self._assemble_context(results)

            # Step 2: Generate proposal with grounding instructions
            system_prompt = """You are an assistant for Canon Builder, helping users extend their worldbuilding canon.

Your task is to generate logical extensions based on existing canonical content.

Rules:
1. Stay consistent with all provided canonical sources
2. Build naturally from established facts
3. Maintain the tone and style of the canon
4. Be creative within established constraints
5. Flag any potential contradictions you notice"""

            user_prompt = f"""Based on the following canonical sources, generate an extension:

Request: {prompt}

Canonical Sources:
{context}

Generate a coherent extension that builds on this canon:"""

            content = await self.ollama_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=creativity_level
            )

            # TODO: Run consistency check and compute coherence score

            return {
                "content": content.strip(),
                "supporting_sources": [s["document_id"] for s in sources],
                "coherence_score": 0.85,  # TODO: Implement scoring
                "potential_contradictions": []  # TODO: Implement detection
            }

        except Exception as e:
            logger.error(f"Error generating extension: {e}")
            raise
