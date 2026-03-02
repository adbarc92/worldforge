from .base import LLMProvider


class LLMService:
    def __init__(self, generator: LLMProvider, embedder: LLMProvider):
        self.generator = generator
        self.embedder = embedder

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        return await self.generator.generate(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self.embedder.embed(texts)

    async def check_available(self) -> dict[str, bool]:
        return {
            "generator": await self.generator.check_available(),
            "embedder": await self.embedder.check_available(),
        }
