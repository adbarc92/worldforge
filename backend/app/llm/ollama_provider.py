"""
Ollama provider implementation for local LLM inference.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import ollama

from .provider import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference."""

    def __init__(
        self,
        base_url: str = "http://ollama:11434",
        model: str = "mistral:7b-instruct",
        temperature: float = 0.0
    ):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama server base URL
            model: Model name to use
            temperature: Default temperature
        """
        self.client = ollama.AsyncClient(host=base_url)
        self.model = model
        self.default_temperature = temperature

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate text completion from prompt."""
        try:
            options = {
                "temperature": temperature if temperature is not None else self.default_temperature
            }
            if max_tokens:
                options["num_predict"] = max_tokens

            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options=options,
                **kwargs
            )
            return response["response"]
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured JSON output matching a schema."""
        # Add schema to prompt and request JSON output
        schema_str = json.dumps(schema, indent=2)
        structured_prompt = f"""{prompt}

Respond with valid JSON matching this schema:
{schema_str}

Output only the JSON, no additional text or explanation."""

        try:
            options = {
                "temperature": temperature if temperature is not None else self.default_temperature
            }
            if max_tokens:
                options["num_predict"] = max_tokens

            response = await self.client.generate(
                model=self.model,
                prompt=structured_prompt,
                options=options,
                format="json",  # Request JSON format from Ollama
                **kwargs
            )

            response_text = response["response"].strip()

            # Extract JSON from response (handle markdown code blocks)
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            return json.loads(response_text.strip())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Ollama response: {e}")
            logger.error(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Ollama: {e}")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    async def generate_with_context(
        self,
        prompt: str,
        context: List[str],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate text with additional context chunks."""
        # Combine context and prompt
        context_text = "\n\n".join([f"Context {i+1}:\n{ctx}" for i, ctx in enumerate(context)])
        full_prompt = f"""{context_text}

User Question:
{prompt}

Based on the context above, provide a detailed answer with citations to the relevant context sections."""

        return await self.generate(
            prompt=full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
