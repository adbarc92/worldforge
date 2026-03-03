import os
import uuid
import aiofiles
from loguru import logger
from llama_index.core.node_parser import SentenceSplitter

from app.core.config import settings
from app.services.llm import LLMService
from app.services.qdrant_service import QdrantService
from app.models.repositories import DocumentRepository


class IngestionService:
    def __init__(
        self,
        llm_service: LLMService,
        qdrant_service: QdrantService,
        document_repo: DocumentRepository,
    ):
        self.llm_service = llm_service
        self.qdrant_service = qdrant_service
        self.document_repo = document_repo
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    async def process_document(self, file_path: str, title: str):
        doc = await self.document_repo.create(title=title, file_path=file_path)
        try:
            await self.document_repo.update_status(doc.id, "processing")

            text = await self._extract_text(file_path)
            if not text.strip():
                raise ValueError("Document is empty after text extraction")

            chunks = self._chunk_text(text, document_id=doc.id, title=title)
            logger.info(f"Document '{title}' split into {len(chunks)} chunks")

            texts = [c["text"] for c in chunks]
            embeddings = await self.llm_service.embed(texts)

            ids = [c["chunk_id"] for c in chunks]
            payloads = [
                {
                    "text": c["text"],
                    "document_id": c["document_id"],
                    "title": c["title"],
                    "chunk_index": c["chunk_index"],
                }
                for c in chunks
            ]
            await self.qdrant_service.upsert(ids=ids, vectors=embeddings, payloads=payloads)

            await self.document_repo.update_status(doc.id, "completed", chunk_count=len(chunks))
            logger.info(f"Document '{title}' processed successfully")
            return doc

        except Exception as e:
            logger.error(f"Failed to process document '{title}': {e}")
            await self.document_repo.update_status(doc.id, "failed", error_message=str(e))
            try:
                await self.qdrant_service.delete_by_document(doc.id)
            except Exception:
                pass
            raise

    async def _extract_text(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()

        if ext in (".txt", ".md"):
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                return await f.read()

        elif ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)

        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _chunk_text(self, text: str, document_id: str, title: str) -> list[dict]:
        splitter = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        text_chunks = splitter.split_text(text)

        return [
            {
                "chunk_id": str(uuid.uuid4()),
                "text": chunk,
                "chunk_index": i,
                "document_id": document_id,
                "title": title,
            }
            for i, chunk in enumerate(text_chunks)
        ]

    async def delete_document(self, doc_id: str) -> bool:
        doc = await self.document_repo.get(doc_id)
        if not doc:
            return False

        await self.qdrant_service.delete_by_document(doc_id)

        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        await self.document_repo.delete(doc_id)
        logger.info(f"Document '{doc.title}' deleted")
        return True
