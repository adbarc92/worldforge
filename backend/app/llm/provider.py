"""
Abstract LLM provider interface for supporting multiple LLM backends.
Enables switching between Claude API and Ollama.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion from prompt.

        Args:
            prompt: The prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text as string
        """
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output matching a schema.

        Args:
            prompt: The prompt text
            schema: JSON schema the output should match
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            Parsed JSON object matching schema
        """
        pass

    @abstractmethod
    async def generate_with_context(
        self,
        prompt: str,
        context: List[str],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate text with additional context chunks.

        Args:
            prompt: The prompt text
            context: List of context strings
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text as string
        """
        pass


def get_llm_provider() -> LLMProvider:
    """
    Factory function to get the configured LLM provider.

    Returns:
        Configured LLM provider instance (ClaudeProvider or OllamaProvider)

    Raises:
        ValueError: If provider is not recognized or not properly configured
    """
    from .claude_provider import ClaudeProvider
    from .ollama_provider import OllamaProvider

    if settings.llm_provider == "claude":
        if not settings.claude_api_key:
            raise ValueError(
                "Claude API key not configured. "
                "Set CLAUDE_API_KEY environment variable."
            )
        return ClaudeProvider(
            api_key=settings.claude_api_key,
            model=settings.claude_model,
            max_tokens=settings.claude_max_tokens,
            temperature=settings.claude_temperature
        )
    elif settings.llm_provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=settings.ollama_temperature
        )
    else:
        raise ValueError(
            f"Unknown LLM provider: {settings.llm_provider}. "
            "Must be 'claude' or 'ollama'."
        )
