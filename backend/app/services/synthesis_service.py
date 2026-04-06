import json
import logging
import re

from app.models.contradiction_repository import ContradictionRepository
from app.models.synthesis_repository import SynthesisRepository
from app.services.llm.service import LLMService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)

CHUNKS_PER_BATCH = 50
SECTION_TOP_K = 30

TOPIC_EXTRACTION_PROMPT = """You are analyzing passages from a worldbuilding canon. Given the following passages, list the major topics covered. Return only a comma-separated list of topic names (e.g., "Cosmogony, Major Characters, Factions, Key Events, Geography").

Passages:
{chunks_text}

Topics:"""

OUTLINE_CONSOLIDATION_PROMPT = """You are organizing topics for a worldbuilding primer document. Given these topic lists extracted from different sections of a canon:

{topic_lists}

Consolidate them into a final ordered outline of 8-15 sections for a comprehensive world primer. Each section should have a title and a one-line description of what it covers.

Return JSON only — an array of objects: [{{"title": "Section Title", "description": "What this section covers"}}]"""

SECTION_GENERATION_PROMPT = """You are writing a section of a worldbuilding primer for newcomers. Write a flowing, engaging narrative about "{title}" ({description}) for someone being introduced to this world for the first time.

Use only the provided source material. Do not invent facts.

{resolution_notes_block}

Source material:
{source_chunks}

Write the section now. Do not include a heading — just the narrative text."""


class SynthesisService:
    def __init__(
        self,
        llm_service: LLMService,
        qdrant_service: QdrantService,
        contradiction_repo: ContradictionRepository,
        synthesis_repo: SynthesisRepository,
    ):
        self.llm_service = llm_service
        self.qdrant_service = qdrant_service
        self.contradiction_repo = contradiction_repo
        self.synthesis_repo = synthesis_repo

    async def check_gate(self, project_id: str) -> None:
        """Raise ValueError if there are unresolved contradictions."""
        count = await self.contradiction_repo.count(project_id, status="open")
        if count > 0:
            raise ValueError(
                f"Cannot synthesize: {count} open contradictions must be resolved first"
            )

    async def generate_outline(self, project_id: str) -> list[dict]:
        """Generate a structured outline by extracting and consolidating topics from all project chunks."""
        # 1. Get all chunks from Qdrant
        chunks = await self.qdrant_service.search_by_filter(
            filters={"project_id": project_id}, limit=10000
        )

        # 2. Raise if no chunks
        if not chunks:
            raise ValueError("No chunks found for this project. Upload documents first.")

        # 3. Batch chunks into groups
        batches = [
            chunks[i : i + CHUNKS_PER_BATCH]
            for i in range(0, len(chunks), CHUNKS_PER_BATCH)
        ]

        # 4. Extract topics from each batch
        topic_lists = []
        for batch in batches:
            chunks_text = "\n\n---\n\n".join(c["text"] for c in batch)
            prompt = TOPIC_EXTRACTION_PROMPT.format(chunks_text=chunks_text)
            topics = await self.llm_service.generate(
                prompt=prompt, temperature=0.3, max_tokens=512
            )
            topic_lists.append(topics.strip())

        # 5. Consolidate into final outline
        combined_topics = "\n\n".join(
            f"Batch {i+1}: {tl}" for i, tl in enumerate(topic_lists)
        )
        consolidation_prompt = OUTLINE_CONSOLIDATION_PROMPT.format(
            topic_lists=combined_topics
        )
        outline_response = await self.llm_service.generate(
            prompt=consolidation_prompt, temperature=0.3, max_tokens=2048
        )

        # 6. Parse and return
        return self._parse_outline_json(outline_response)

    def _parse_outline_json(self, response: str) -> list[dict]:
        """Parse JSON array from LLM response, handling markdown fences."""
        text = response.strip()
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
        try:
            data = json.loads(text)
            if not isinstance(data, list):
                raise ValueError("Expected a JSON array")
            return [
                {"title": item["title"], "description": item["description"]}
                for item in data
            ]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"Failed to parse outline JSON: {exc}") from exc

    async def generate_section(self, project_id: str, section: dict) -> str:
        """Generate a single primer section using relevant chunks and resolution notes."""
        # 1. Embed section title+description, search Qdrant top-K
        query_text = f"{section['title']} {section['description']}"
        vectors = await self.llm_service.embed([query_text])
        results = await self.qdrant_service.search(
            query_vector=vectors[0],
            top_k=SECTION_TOP_K,
            filters={"project_id": project_id},
        )
        source_chunks = "\n\n---\n\n".join(
            r["payload"]["text"] for r in results
        )

        # 2. Get resolved contradictions with resolution notes
        resolved = await self.contradiction_repo.list(
            project_id, status="resolved", skip=0, limit=1000
        )
        notes = [
            c for c in resolved if c.resolution_note
        ]

        resolution_notes_block = ""
        if notes:
            lines = []
            for c in notes:
                lines.append(
                    f'- Conflict: "{c.chunk_a_text[:100]}..." vs "{c.chunk_b_text[:100]}..." '
                    f"\u2192 Resolution: {c.resolution_note}"
                )
            resolution_notes_block = (
                "Important resolution notes from the canon maintainer:\n"
                + "\n".join(lines)
            )

        # 3. Build prompt
        prompt = SECTION_GENERATION_PROMPT.format(
            title=section["title"],
            description=section["description"],
            resolution_notes_block=resolution_notes_block,
            source_chunks=source_chunks,
        )

        # 4. Generate
        content = await self.llm_service.generate(
            prompt=prompt, temperature=0.7, max_tokens=4096
        )

        # 5. Return stripped content
        return content.strip()

    def assemble_document(self, sections: list[dict]) -> str:
        """Join generated sections into a full markdown primer document."""
        parts = []
        for section in sections:
            parts.append(f"# {section['title']}\n\n{section['content']}")
        return "\n\n---\n\n".join(parts)

    async def run_outline_generation(
        self, synthesis_id: str, project_id: str, auto: bool = False
    ) -> None:
        """Run outline generation, updating synthesis status along the way."""
        try:
            outline = await self.generate_outline(project_id)
            if auto:
                await self.synthesis_repo.update_status(
                    synthesis_id,
                    status="outline_approved",
                    outline=outline,
                    outline_approved=True,
                )
                await self.run_section_generation(synthesis_id, project_id)
            else:
                await self.synthesis_repo.update_status(
                    synthesis_id,
                    status="outline_ready",
                    outline=outline,
                )
        except Exception as exc:
            logger.exception("Outline generation failed for synthesis %s", synthesis_id)
            await self.synthesis_repo.update_status(
                synthesis_id,
                status="failed",
                error_message=str(exc),
            )

    async def run_section_generation(
        self, synthesis_id: str, project_id: str
    ) -> None:
        """Generate all sections and assemble the final document."""
        try:
            synthesis = await self.synthesis_repo.get(synthesis_id)
            if not synthesis:
                raise ValueError(f"Synthesis {synthesis_id} not found")

            await self.synthesis_repo.update_status(
                synthesis_id, status="generating"
            )

            sections = []
            for section_def in synthesis.outline:
                content = await self.generate_section(project_id, section_def)
                sections.append(
                    {"title": section_def["title"], "content": content}
                )

            document = self.assemble_document(sections)

            await self.synthesis_repo.update_status(
                synthesis_id,
                status="completed",
                content=document,
            )
        except Exception as exc:
            logger.exception("Section generation failed for synthesis %s", synthesis_id)
            await self.synthesis_repo.update_status(
                synthesis_id,
                status="failed",
                error_message=str(exc),
            )
