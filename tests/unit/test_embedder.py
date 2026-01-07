"""
Unit tests for embedder.
Tests: TEST-UNIT-009 through TEST-UNIT-011
"""

import pytest
import numpy as np
from backend.app.ingestion.embedder import Embedder, get_embedder


class TestEmbedder:
    """Test suite for Embedder class."""

    @pytest.mark.slow
    def test_embedder_initialization(self):
        """Test embedder can be initialized."""
        embedder = Embedder()
        assert embedder is not None
        assert embedder.model is not None
        assert embedder.embedding_dim == 1024  # BGE-large-en-v1.5

    def test_get_embedding_dim(self):
        """Test getting embedding dimension."""
        embedder = get_embedder()
        dim = embedder.get_embedding_dim()
        assert dim == 1024

    # TEST-UNIT-009: Generate Single Embedding
    @pytest.mark.unit
    @pytest.mark.slow
    def test_generate_single_embedding(self):
        """Test embedding generation for single text."""
        embedder = get_embedder()
        text = "This is a test sentence for embedding."

        embedding = embedder.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 1024  # BGE-large-en-v1.5 dimension
        assert all(isinstance(x, float) for x in embedding)

        # Embeddings should have reasonable values
        assert all(-10 < x < 10 for x in embedding)

    # TEST-UNIT-010: Generate Batch Embeddings
    @pytest.mark.unit
    @pytest.mark.slow
    def test_generate_batch_embeddings(self):
        """Test batch embedding generation."""
        embedder = get_embedder()
        texts = ["Text one", "Text two", "Text three"]

        embeddings = embedder.embed_batch(texts, show_progress=False)

        assert len(embeddings) == 3
        assert all(len(emb) == 1024 for emb in embeddings)
        assert all(isinstance(emb, list) for emb in embeddings)

    @pytest.mark.unit
    @pytest.mark.slow
    def test_embed_list_of_texts(self):
        """Test embedding a list of texts using embed()."""
        embedder = get_embedder()
        texts = ["First text", "Second text"]

        embeddings = embedder.embed(texts)

        assert len(embeddings) == 2
        assert all(len(emb) == 1024 for emb in embeddings)

    @pytest.mark.unit
    def test_embed_empty_string(self):
        """Test embedding handles empty string."""
        embedder = get_embedder()

        embedding = embedder.embed("")

        # Should still return an embedding
        assert isinstance(embedding, list)
        assert len(embedding) == 1024

    # TEST-UNIT-011: Embedding Similarity
    @pytest.mark.unit
    @pytest.mark.slow
    def test_embedding_similarity(self):
        """Test that similar texts have similar embeddings."""
        embedder = get_embedder()

        text1 = "The quick brown fox jumps over the lazy dog."
        text2 = "A fast brown fox leaps over a sleepy dog."
        text3 = "Python is a programming language."

        emb1 = embedder.embed(text1)
        emb2 = embedder.embed(text2)
        emb3 = embedder.embed(text3)

        def cosine_sim(a, b):
            a = np.array(a)
            b = np.array(b)
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        sim_1_2 = cosine_sim(emb1, emb2)
        sim_1_3 = cosine_sim(emb1, emb3)

        # Similar texts should be more similar than dissimilar texts
        assert sim_1_2 > sim_1_3
        assert sim_1_2 > 0.7  # Should be quite similar

    @pytest.mark.unit
    @pytest.mark.slow
    def test_embedding_consistency(self):
        """Test that same text produces same embedding."""
        embedder = get_embedder()

        text = "Consistent text for embedding."

        emb1 = embedder.embed(text)
        emb2 = embedder.embed(text)

        # Should be identical (or very close due to floating point)
        assert len(emb1) == len(emb2)

        # Calculate similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        assert similarity > 0.9999  # Should be essentially identical

    @pytest.mark.unit
    @pytest.mark.slow
    def test_embed_batch_with_progress(self):
        """Test batch embedding with progress bar."""
        embedder = get_embedder()

        # Create batch large enough to show progress
        texts = [f"Test sentence number {i}" for i in range(20)]

        embeddings = embedder.embed_batch(texts, batch_size=5, show_progress=False)

        assert len(embeddings) == 20
        assert all(len(emb) == 1024 for emb in embeddings)

    @pytest.mark.unit
    @pytest.mark.slow
    def test_embed_batch_custom_batch_size(self):
        """Test batch embedding with custom batch size."""
        embedder = get_embedder()

        texts = [f"Sentence {i}" for i in range(10)]

        embeddings = embedder.embed_batch(texts, batch_size=3, show_progress=False)

        assert len(embeddings) == 10

    def test_get_embedder_singleton(self):
        """Test that get_embedder returns same instance."""
        embedder1 = get_embedder()
        embedder2 = get_embedder()

        # Should be the same instance (singleton pattern)
        assert embedder1 is embedder2


class TestEmbedderEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.unit
    def test_embed_very_long_text(self):
        """Test embedding handles very long text."""
        embedder = get_embedder()

        # Create very long text (>10k characters)
        long_text = "Lorem ipsum dolor sit amet. " * 500

        embedding = embedder.embed(long_text)

        # Should still produce valid embedding
        assert isinstance(embedding, list)
        assert len(embedding) == 1024

    @pytest.mark.unit
    def test_embed_special_characters(self):
        """Test embedding handles special characters."""
        embedder = get_embedder()

        text = "Special chars: @#$%^&*()_+-=[]{}|;':\",./<>?"

        embedding = embedder.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 1024

    @pytest.mark.unit
    def test_embed_unicode_text(self):
        """Test embedding handles Unicode characters."""
        embedder = get_embedder()

        text = "Unicode: 你好世界 🌍 Здравствуй мир"

        embedding = embedder.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 1024

    @pytest.mark.unit
    def test_embed_newlines_and_tabs(self):
        """Test embedding handles newlines and tabs."""
        embedder = get_embedder()

        text = "Line 1\nLine 2\n\tIndented line"

        embedding = embedder.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 1024
