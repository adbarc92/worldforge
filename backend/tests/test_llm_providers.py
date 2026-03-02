"""Tests for LLM provider abstraction layer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm import AnthropicProvider, OpenAIProvider, LLMService


@pytest.fixture
def anthropic_provider():
    """Create an AnthropicProvider with a fake API key."""
    with patch("app.services.llm.anthropic_provider.anthropic") as mock_anthropic:
        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        provider = AnthropicProvider(
            api_key="fake-key", model="claude-sonnet-4-20250514"
        )
        provider.client = mock_client
        yield provider


@pytest.fixture
def openai_provider():
    """Create an OpenAIProvider with a fake API key."""
    with patch("app.services.llm.openai_provider.openai") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.AsyncOpenAI.return_value = mock_client
        provider = OpenAIProvider(
            api_key="fake-key",
            model="text-embedding-3-large",
            dimensions=3072,
        )
        provider.client = mock_client
        yield provider


@pytest.mark.asyncio
async def test_anthropic_generate(anthropic_provider):
    """Test that AnthropicProvider.generate calls the API and returns text."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Generated response")]
    anthropic_provider.client.messages.create = AsyncMock(return_value=mock_response)

    result = await anthropic_provider.generate(
        prompt="Tell me about dragons",
        system_prompt="You are a worldbuilding assistant.",
        temperature=0.5,
        max_tokens=1024,
    )

    assert result == "Generated response"
    anthropic_provider.client.messages.create.assert_called_once_with(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        temperature=0.5,
        messages=[{"role": "user", "content": "Tell me about dragons"}],
        system="You are a worldbuilding assistant.",
    )


@pytest.mark.asyncio
async def test_anthropic_generate_no_system_prompt(anthropic_provider):
    """Test generate without a system prompt omits the system kwarg."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Response without system")]
    anthropic_provider.client.messages.create = AsyncMock(return_value=mock_response)

    result = await anthropic_provider.generate(prompt="Hello")

    assert result == "Response without system"
    call_kwargs = anthropic_provider.client.messages.create.call_args[1]
    assert "system" not in call_kwargs


@pytest.mark.asyncio
async def test_anthropic_embed_raises(anthropic_provider):
    """Test that AnthropicProvider.embed raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="does not support embeddings"):
        await anthropic_provider.embed(["some text"])


@pytest.mark.asyncio
async def test_anthropic_check_available(anthropic_provider):
    """Test availability check returns True on success."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="hi")]
    anthropic_provider.client.messages.create = AsyncMock(return_value=mock_response)

    assert await anthropic_provider.check_available() is True


@pytest.mark.asyncio
async def test_anthropic_check_available_failure(anthropic_provider):
    """Test availability check returns False on exception."""
    anthropic_provider.client.messages.create = AsyncMock(
        side_effect=Exception("API error")
    )

    assert await anthropic_provider.check_available() is False


@pytest.mark.asyncio
async def test_openai_embed(openai_provider):
    """Test that OpenAIProvider.embed calls the API and returns vectors."""
    mock_embedding_1 = MagicMock(embedding=[0.1, 0.2, 0.3])
    mock_embedding_2 = MagicMock(embedding=[0.4, 0.5, 0.6])
    mock_response = MagicMock(data=[mock_embedding_1, mock_embedding_2])
    openai_provider.client.embeddings.create = AsyncMock(return_value=mock_response)

    result = await openai_provider.embed(["hello", "world"])

    assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    openai_provider.client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-large",
        input=["hello", "world"],
        dimensions=3072,
    )


@pytest.mark.asyncio
async def test_openai_generate_raises(openai_provider):
    """Test that OpenAIProvider.generate raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="embeddings only"):
        await openai_provider.generate("Hello")


@pytest.mark.asyncio
async def test_openai_check_available(openai_provider):
    """Test availability check returns True on success."""
    mock_response = MagicMock(data=[MagicMock(embedding=[0.0])])
    openai_provider.client.embeddings.create = AsyncMock(return_value=mock_response)

    assert await openai_provider.check_available() is True


@pytest.mark.asyncio
async def test_openai_check_available_failure(openai_provider):
    """Test availability check returns False on exception."""
    openai_provider.client.embeddings.create = AsyncMock(
        side_effect=Exception("API error")
    )

    assert await openai_provider.check_available() is False


@pytest.mark.asyncio
async def test_llm_service_routes_generate():
    """Test that LLMService.generate delegates to the generator provider."""
    mock_generator = AsyncMock()
    mock_generator.generate = AsyncMock(return_value="Generated text")
    mock_embedder = AsyncMock()

    service = LLMService(generator=mock_generator, embedder=mock_embedder)
    result = await service.generate(
        prompt="What is magic?",
        system_prompt="You are helpful.",
        temperature=0.7,
        max_tokens=512,
    )

    assert result == "Generated text"
    mock_generator.generate.assert_called_once_with(
        "What is magic?",
        system_prompt="You are helpful.",
        temperature=0.7,
        max_tokens=512,
    )
    mock_embedder.generate.assert_not_called()


@pytest.mark.asyncio
async def test_llm_service_routes_embed():
    """Test that LLMService.embed delegates to the embedder provider."""
    mock_generator = AsyncMock()
    mock_embedder = AsyncMock()
    mock_embedder.embed = AsyncMock(return_value=[[0.1, 0.2]])

    service = LLMService(generator=mock_generator, embedder=mock_embedder)
    result = await service.embed(["some text"])

    assert result == [[0.1, 0.2]]
    mock_embedder.embed.assert_called_once_with(["some text"])
    mock_generator.embed.assert_not_called()


@pytest.mark.asyncio
async def test_llm_service_check_available():
    """Test that LLMService.check_available checks both providers."""
    mock_generator = AsyncMock()
    mock_generator.check_available = AsyncMock(return_value=True)
    mock_embedder = AsyncMock()
    mock_embedder.check_available = AsyncMock(return_value=False)

    service = LLMService(generator=mock_generator, embedder=mock_embedder)
    result = await service.check_available()

    assert result == {"generator": True, "embedder": False}
