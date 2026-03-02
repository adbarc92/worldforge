import openai

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, dimensions: int = 3072):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        raise NotImplementedError("OpenAI provider is configured for embeddings only")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions,
        )
        return [item.embedding for item in response.data]

    async def check_available(self) -> bool:
        try:
            await self.client.embeddings.create(
                model=self.model,
                input=["test"],
                dimensions=self.dimensions,
            )
            return True
        except Exception:
            return False
