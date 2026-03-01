"""
Ollama service for local LLM inference
"""
from typing import List, Dict, Any
import httpx
from loguru import logger

from app.core.config import settings


class OllamaService:
    """Service for interacting with Ollama local LLM"""

    def __init__(self):
        """Initialize Ollama client"""
        self.base_url = settings.OLLAMA_URL
        self.llm_model = settings.LLM_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """
        Generate text using Ollama LLM

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        temperature = temperature or settings.LLM_TEMPERATURE
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                payload = {
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }

                if system_prompt:
                    payload["system"] = system_prompt

                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()

                result = response.json()
                return result.get("response", "")

            except Exception as e:
                logger.error(f"Error generating with Ollama: {e}")
                raise

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for text

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text
                    }
                )
                response.raise_for_status()

                result = response.json()
                return result.get("embedding", [])

            except Exception as e:
                logger.error(f"Error generating embedding with Ollama: {e}")
                raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)

        return embeddings

    async def check_model_availability(self, model_name: str = None) -> bool:
        """
        Check if a model is available in Ollama

        Args:
            model_name: Model to check (defaults to configured LLM)

        Returns:
            True if model is available
        """
        model_name = model_name or self.llm_model

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()

                result = response.json()
                models = [m["name"] for m in result.get("models", [])]

                return model_name in models

            except Exception as e:
                logger.error(f"Error checking Ollama models: {e}")
                return False
