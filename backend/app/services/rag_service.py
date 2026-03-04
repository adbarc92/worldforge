import time

import tiktoken
from loguru import logger

from app.core.config import settings
from app.services.llm.service import LLMService
from app.services.qdrant_service import QdrantService

SYSTEM_PROMPT = """You are a knowledgeable assistant for a worldbuilding canon.
Answer questions using ONLY the provided source material.
If the sources don't contain enough information, say so clearly.
Always reference which sources support your answer."""

NO_CONTEXT_PROMPT = """You are a knowledgeable assistant for a worldbuilding canon.
The user asked a question but no relevant source material was found in the canon.
Politely inform them that you couldn't find relevant information in the current canon documents."""


class RAGService:
    def __init__(self, llm_service: LLMService, qdrant_service: QdrantService):
        self.llm_service = llm_service
        self.qdrant_service = qdrant_service
        self.max_context_tokens = settings.CONTEXT_MAX_TOKENS

    async def query(self, question: str, top_k: int = 10, project_id: str | None = None) -> dict:
        start = time.time()

        query_embedding = (await self.llm_service.embed([question]))[0]

        filters = None
        if project_id:
            filters = {"project_id": project_id}

        results = await self.qdrant_service.search(
            query_vector=query_embedding,
            top_k=top_k,
            filters=filters,
        )

        context, citations = self._assemble_context(results)

        if context:
            prompt = f"Question: {question}\n\nSources:\n{context}\n\nAnswer the question based on the sources above."
            answer = await self.llm_service.generate(
                prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3
            )
        else:
            prompt = f"Question: {question}"
            answer = await self.llm_service.generate(
                prompt, system_prompt=NO_CONTEXT_PROMPT, temperature=0.3
            )

        elapsed_ms = int((time.time() - start) * 1000)

        return {
            "answer": answer,
            "citations": citations,
            "processing_time_ms": elapsed_ms,
        }

    def _assemble_context(self, results: list[dict]) -> tuple[str, list[dict]]:
        if not results:
            return "", []

        try:
            enc = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")

        context_parts: list[str] = []
        citations: list[dict] = []
        total_tokens = 0

        for i, result in enumerate(results):
            payload = result["payload"]
            text = payload.get("text", "")
            chunk_tokens = len(enc.encode(text))

            if total_tokens + chunk_tokens > self.max_context_tokens:
                break

            total_tokens += chunk_tokens
            context_parts.append(f"[Source {i + 1}]\n{text}")
            citations.append(
                {
                    "document_id": payload.get("document_id", ""),
                    "title": payload.get("title", ""),
                    "chunk_text": text[:200],
                    "relevance_score": result.get("score", 0.0),
                }
            )

        return "\n\n".join(context_parts), citations
