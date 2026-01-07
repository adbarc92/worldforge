"""
Claude API provider implementation using Anthropic SDK.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import anthropic

from .provider import LLMProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    """Claude API provider using Anthropic SDK."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.0
    ):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Default max tokens
            temperature: Default temperature
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.default_max_tokens = max_tokens
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
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.default_max_tokens,
                temperature=temperature if temperature is not None else self.default_temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
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

Output only the JSON, no additional text."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.default_max_tokens,
                temperature=temperature if temperature is not None else self.default_temperature,
                messages=[{"role": "user", "content": structured_prompt}],
                **kwargs
            )

            response_text = response.content[0].text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```

            return json.loads(response_text.strip())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            logger.error(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")
        except Exception as e:
            logger.error(f"Claude API error: {e}")
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
