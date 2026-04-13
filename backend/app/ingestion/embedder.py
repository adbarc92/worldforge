"""
Embedding generator using BGE-large-en-v1.5 model.
Creates vector embeddings for semantic search.
"""

import logging
from typing import List, Union
from sentence_transformers import SentenceTransformer

from ..config import settings

logger = logging.getLogger(__name__)


class Embedder:
    """Generate embeddings using BGE-large-en-v1.5 sentence transformer."""

    def __init__(
        self,
        model_name: str = None,
        device: str = None
    ):
        """
        Initialize embedder with sentence transformer model.

        Args:
            model_name: Name of the sentence transformer model
            device: Device to use ('cpu' or 'cuda')
        """
        self.model_name = model_name or settings.embeddings_model
        self.device = device or settings.embeddings_device

        logger.info(f"Loading embedding model: {self.model_name} on {self.device}")

        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text or list of texts.

        Args:
            text: Single text string or list of texts

        Returns:
            Embedding vector(s) as list(s) of floats
        """
        try:
            # Handle single string
            if isinstance(text, str):
                embedding = self.model.encode(
                    text,
                    convert_to_numpy=True,
                    show_progress_bar=False
                )
                return embedding.tolist()

            # Handle list of strings
            elif isinstance(text, list):
                embeddings = self.model.encode(
                    text,
                    convert_to_numpy=True,
                    show_progress_bar=len(text) > 10,  # Show progress for large batches
                    batch_size=32
                )
                return embeddings.tolist()

            else:
                raise ValueError(f"Text must be str or List[str], got {type(text)}")

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts with progress tracking.

        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")

            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=show_progress,
                batch_size=batch_size
            )

            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Error in batch embedding: {e}")
            raise

    def get_embedding_dim(self) -> int:
        """
        Get the embedding dimension.

        Returns:
            Embedding vector dimension
        """
        return self.embedding_dim


# Global embedder instance (lazy-loaded)
_embedder_instance = None


def get_embedder() -> Embedder:
    """
    Get or create global embedder instance.

    Returns:
        Singleton Embedder instance
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder()
    return _embedder_instance
