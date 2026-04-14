import json
import logging
import re

from app.models.contradiction_repository import ContradictionRepository
from app.services.llm.service import LLMService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are comparing passages from a worldbuilding canon. Do these two passages contradict each other? A contradiction means they assert mutually exclusive facts about the same subject. Different levels of detail, different topics, or evolving ideas are NOT contradictions.

Passage A:
{chunk_a_text}

Passage B:
{chunk_b_text}

Respond with JSON only: {{"is_contradiction": bool, "explanation": "string"}}"""

SIMILAR_CHUNKS_TOP_K = 5


class ContradictionService:
    def __init__(
        self,
        llm_service: LLMService,
        qdrant_service: QdrantService,
        repo: ContradictionRepository,
    ):
        self.llm_service = llm_service
        self.qdrant_service = qdrant_service
        self.repo = repo

    async def classify_pair(self, chunk_a_text: str, chunk_b_text: str) -> dict:
        """Ask the LLM whether two passages contradict each other."""
        prompt = CLASSIFICATION_PROMPT.format(
            chunk_a_text=chunk_a_text,
            chunk_b_text=chunk_b_text,
        )
        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=0,
                max_tokens=256,
            )
            return self._parse_classification(response)
        except Exception:
            logger.exception("LLM classification failed")
            return {"is_contradiction": False, "explanation": ""}

    def _parse_classification(self, response: str) -> dict:
        """Parse LLM JSON response, handling markdown wrapping."""
        text = response.strip()
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
        try:
            data = json.loads(text)
            return {
                "is_contradiction": bool(data.get("is_contradiction", False)),
                "explanation": str(data.get("explanation", "")),
            }
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Failed to parse LLM classification response: %s", response[:200])
            return {"is_contradiction": False, "explanation": ""}

    async def _get_document_chunks(self, document_id: str) -> list[dict]:
        """Retrieve all chunks for a document from Qdrant."""
        return await self.qdrant_service.search_by_filter(
            filters={"document_id": document_id},
            limit=1000,
        )

    async def scan_document(self, document_id: str, project_id: str) -> int:
        """Scan a single document's chunks against the rest of the project. Returns count of new contradictions found."""
        chunks = await self._get_document_chunks(document_id)
        if not chunks:
            return 0

        found = 0
        for chunk in chunks:
            try:
                chunk_vector = await self.llm_service.embed([chunk["text"]])
                similar = await self.qdrant_service.search(
                    query_vector=chunk_vector[0],
                    top_k=SIMILAR_CHUNKS_TOP_K,
                    filters={"project_id": project_id},
                )

                for match in similar:
                    match_doc_id = match["payload"].get("document_id", "")
                    if match_doc_id == document_id:
                        continue

                    if await self.repo.pair_exists(chunk["id"], match["id"]):
                        continue

                    classification = await self.classify_pair(
                        chunk["text"],
                        match["payload"]["text"],
                    )

                    if classification["is_contradiction"]:
                        await self.repo.create(
                            project_id=project_id,
                            chunk_a_id=chunk["id"],
                            chunk_b_id=match["id"],
                            document_a_id=document_id,
                            document_b_id=match_doc_id,
                            document_a_title=chunk.get("title", ""),
                            document_b_title=match["payload"].get("title", ""),
                            chunk_a_text=chunk["text"],
                            chunk_b_text=match["payload"]["text"],
                            explanation=classification["explanation"],
                        )
                        found += 1
            except Exception:
                logger.exception("Failed to process chunk %s, skipping", chunk["id"])
                continue

        logger.info("Scanned document %s: found %d contradictions", document_id, found)
        return found

    async def scan_project(self, project_id: str) -> int:
        """Scan all documents in a project for contradictions."""
        from app.models.repositories import DocumentRepository
        doc_repo = DocumentRepository(self.repo.session)
        documents = await doc_repo.list(project_id=project_id, skip=0, limit=10000)

        total = 0
        for doc in documents:
            if doc.status != "completed":
                continue
            count = await self.scan_document(doc.id, project_id)
            total += count

        logger.info("Project scan complete for %s: found %d total contradictions", project_id, total)
        return total
