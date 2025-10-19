"""Embedding generation utilities for MineContext-v2."""

from typing import List, Optional, Tuple

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from backend.config import settings


class EmbeddingService:
    """Service for generating text embeddings using sentence transformers."""

    def __init__(self, model_name: Optional[str] = None):
        """Initialize embedding service.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name or settings.embeddings.model
        self.model: Optional[SentenceTransformer] = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the sentence transformer model."""
        if not settings.embeddings.enabled:
            logger.warning("Embeddings are disabled in configuration")
            return

        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model loaded successfully. Dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None

    def is_available(self) -> bool:
        """Check if embedding service is available.

        Returns:
            True if model is loaded and ready
        """
        return self.model is not None and settings.embeddings.enabled

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model.

        Returns:
            Embedding dimension size
        """
        if not self.is_available():
            return 0
        return self.model.get_sentence_embedding_dimension()

    def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Numpy array of embedding vector, or None if failed
        """
        if not self.is_available():
            logger.warning("Embedding service not available")
            return None

        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def generate_embeddings_batch(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> Tuple[List[np.ndarray], List[int]]:
        """Generate embeddings for multiple texts in batch.

        Args:
            texts: List of input texts
            batch_size: Batch size for processing (uses config default if None)

        Returns:
            Tuple of (successful embeddings list, failed indices list)
        """
        if not self.is_available():
            logger.warning("Embedding service not available")
            return [], list(range(len(texts)))

        batch_size = batch_size or settings.embeddings.batch_size
        embeddings = []
        failed_indices = []

        try:
            # Filter out empty texts and keep track of indices
            valid_texts = []
            valid_indices = []

            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_indices.append(i)
                else:
                    failed_indices.append(i)

            if not valid_texts:
                logger.warning("No valid texts provided for batch embedding")
                return [], failed_indices

            # Generate embeddings in batches
            logger.info(f"Generating embeddings for {len(valid_texts)} texts in batches of {batch_size}")

            all_embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(valid_texts) > 10
            )

            embeddings = list(all_embeddings)
            logger.info(f"Successfully generated {len(embeddings)} embeddings")

        except Exception as e:
            logger.error(f"Error in batch embedding generation: {e}")
            failed_indices = list(range(len(texts)))
            embeddings = []

        return embeddings, failed_indices

    def compute_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Normalize vectors
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            # Compute cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)

            # Clip to [0, 1] range (cosine similarity can be [-1, 1])
            similarity = (similarity + 1) / 2

            return float(similarity)

        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0

    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5,
        min_similarity: Optional[float] = None
    ) -> List[Tuple[int, float]]:
        """Find most similar embeddings to query.

        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        min_similarity = min_similarity or settings.vector_db.similarity_threshold

        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.compute_similarity(query_embedding, candidate)
            if similarity >= min_similarity:
                similarities.append((i, similarity))

        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


# Global embedding service instance
embedding_service = EmbeddingService()
