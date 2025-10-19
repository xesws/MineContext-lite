"""Vector store operations using ChromaDB for MineContext-v2."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import chromadb
import numpy as np
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from backend.config import settings
from backend.utils.embedding_utils import embedding_service


class VectorStore:
    """ChromaDB vector store for screenshot context embeddings."""

    def __init__(self):
        """Initialize vector store."""
        self.client: Optional[chromadb.Client] = None
        self.collection: Optional[chromadb.Collection] = None
        self._initialize()

    def _initialize(self):
        """Initialize ChromaDB client and collection."""
        if not settings.vector_db.enabled:
            logger.warning("Vector database is disabled in configuration")
            return

        try:
            # Ensure vector DB directory exists
            from pathlib import Path
            Path(settings.vector_db.path).mkdir(parents=True, exist_ok=True)

            # Initialize ChromaDB client with persistent storage
            logger.info(f"Initializing ChromaDB at {settings.vector_db.path}")

            self.client = chromadb.PersistentClient(
                path=settings.vector_db.path,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            collection_name = settings.vector_db.collection_name

            try:
                self.collection = self.client.get_collection(name=collection_name)
                logger.info(f"Loaded existing collection '{collection_name}' with {self.collection.count()} items")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "Screenshot context embeddings"}
                )
                logger.info(f"Created new collection '{collection_name}'")

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            self.client = None
            self.collection = None

    def is_available(self) -> bool:
        """Check if vector store is available.

        Returns:
            True if ChromaDB is ready
        """
        return self.collection is not None and settings.vector_db.enabled

    def add_embedding(
        self,
        screenshot_id: int,
        embedding: np.ndarray,
        description: str,
        tags: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Add a screenshot embedding to the vector store.

        Args:
            screenshot_id: Screenshot ID
            embedding: Embedding vector
            description: Screenshot description
            tags: Screenshot tags
            timestamp: Screenshot timestamp

        Returns:
            True if successful
        """
        if not self.is_available():
            logger.warning("Vector store not available")
            return False

        try:
            # Convert numpy array to list for ChromaDB
            embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding

            # Prepare metadata
            metadata = {
                "description": description or "",
                "tags": tags or "",
                "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat()
            }

            # Add to collection
            self.collection.add(
                ids=[f"screenshot_{screenshot_id}"],
                embeddings=[embedding_list],
                metadatas=[metadata]
            )

            logger.debug(f"Added embedding for screenshot {screenshot_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding embedding for screenshot {screenshot_id}: {e}")
            return False

    def add_embeddings_batch(
        self,
        screenshot_ids: List[int],
        embeddings: List[np.ndarray],
        descriptions: List[str],
        tags_list: Optional[List[str]] = None,
        timestamps: Optional[List[datetime]] = None
    ) -> Tuple[int, int]:
        """Add multiple screenshot embeddings in batch.

        Args:
            screenshot_ids: List of screenshot IDs
            embeddings: List of embedding vectors
            descriptions: List of descriptions
            tags_list: Optional list of tags
            timestamps: Optional list of timestamps

        Returns:
            Tuple of (success_count, failure_count)
        """
        if not self.is_available():
            logger.warning("Vector store not available")
            return 0, len(screenshot_ids)

        if not screenshot_ids:
            return 0, 0

        try:
            # Prepare data
            ids = [f"screenshot_{sid}" for sid in screenshot_ids]
            embedding_lists = [
                emb.tolist() if isinstance(emb, np.ndarray) else emb
                for emb in embeddings
            ]

            metadatas = []
            for i, desc in enumerate(descriptions):
                metadata = {
                    "description": desc or "",
                    "tags": tags_list[i] if tags_list and i < len(tags_list) else "",
                    "timestamp": (
                        timestamps[i].isoformat()
                        if timestamps and i < len(timestamps)
                        else datetime.now().isoformat()
                    )
                }
                metadatas.append(metadata)

            # Add batch to collection
            self.collection.add(
                ids=ids,
                embeddings=embedding_lists,
                metadatas=metadatas
            )

            logger.info(f"Added {len(screenshot_ids)} embeddings to vector store")
            return len(screenshot_ids), 0

        except Exception as e:
            logger.error(f"Error adding batch embeddings: {e}")
            return 0, len(screenshot_ids)

    def search_similar(
        self,
        query_embedding: np.ndarray,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None
    ) -> List[Dict]:
        """Search for similar screenshots using embedding.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of result dictionaries with screenshot_id, similarity, and metadata
        """
        if not self.is_available():
            logger.warning("Vector store not available")
            return []

        try:
            top_k = top_k or settings.vector_db.max_results
            min_similarity = min_similarity or settings.vector_db.similarity_threshold

            # Convert numpy array to list
            query_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding

            # Query collection
            results = self.collection.query(
                query_embeddings=[query_list],
                n_results=top_k * 2  # Get more results to filter by threshold
            )

            # Process results
            similar_items = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i, screenshot_id_str in enumerate(results['ids'][0]):
                    # Extract screenshot ID
                    screenshot_id = int(screenshot_id_str.replace("screenshot_", ""))

                    # Get distance and convert to similarity (ChromaDB returns L2 distance)
                    distance = results['distances'][0][i]
                    # Convert L2 distance to cosine similarity approximation
                    similarity = 1 / (1 + distance)

                    # Filter by minimum similarity
                    if similarity >= min_similarity:
                        metadata = results['metadatas'][0][i]
                        similar_items.append({
                            "screenshot_id": screenshot_id,
                            "similarity": float(similarity),
                            "description": metadata.get("description", ""),
                            "tags": metadata.get("tags", ""),
                            "timestamp": metadata.get("timestamp", "")
                        })

            # Sort by similarity (descending) and limit to top_k
            similar_items.sort(key=lambda x: x['similarity'], reverse=True)
            return similar_items[:top_k]

        except Exception as e:
            logger.error(f"Error searching similar screenshots: {e}")
            return []

    def search_by_text(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None
    ) -> List[Dict]:
        """Search for similar screenshots using text query.

        Args:
            query_text: Text query
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of result dictionaries
        """
        if not embedding_service.is_available():
            logger.warning("Embedding service not available")
            return []

        # Generate embedding for query text
        query_embedding = embedding_service.generate_embedding(query_text)
        if query_embedding is None:
            return []

        return self.search_similar(query_embedding, top_k, min_similarity)

    def get_by_id(self, screenshot_id: int) -> Optional[Dict]:
        """Get embedding and metadata by screenshot ID.

        Args:
            screenshot_id: Screenshot ID

        Returns:
            Dictionary with embedding and metadata, or None if not found
        """
        if not self.is_available():
            return None

        try:
            result = self.collection.get(
                ids=[f"screenshot_{screenshot_id}"],
                include=["embeddings", "metadatas"]
            )

            if result and result['ids']:
                return {
                    "screenshot_id": screenshot_id,
                    "embedding": np.array(result['embeddings'][0]),
                    "metadata": result['metadatas'][0]
                }

            return None

        except Exception as e:
            logger.error(f"Error getting embedding for screenshot {screenshot_id}: {e}")
            return None

    def update_embedding(
        self,
        screenshot_id: int,
        embedding: Optional[np.ndarray] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None
    ) -> bool:
        """Update embedding or metadata for a screenshot.

        Args:
            screenshot_id: Screenshot ID
            embedding: New embedding vector (optional)
            description: New description (optional)
            tags: New tags (optional)

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            # Get current data
            current = self.get_by_id(screenshot_id)
            if not current:
                logger.warning(f"Screenshot {screenshot_id} not found in vector store")
                return False

            # Update metadata
            metadata = current['metadata'].copy()
            if description is not None:
                metadata['description'] = description
            if tags is not None:
                metadata['tags'] = tags

            # Update in collection
            update_data = {
                "ids": [f"screenshot_{screenshot_id}"],
                "metadatas": [metadata]
            }

            if embedding is not None:
                embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
                update_data["embeddings"] = [embedding_list]

            self.collection.update(**update_data)

            logger.debug(f"Updated embedding for screenshot {screenshot_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating embedding for screenshot {screenshot_id}: {e}")
            return False

    def delete_embedding(self, screenshot_id: int) -> bool:
        """Delete embedding for a screenshot.

        Args:
            screenshot_id: Screenshot ID

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            self.collection.delete(ids=[f"screenshot_{screenshot_id}"])
            logger.debug(f"Deleted embedding for screenshot {screenshot_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting embedding for screenshot {screenshot_id}: {e}")
            return False

    def get_count(self) -> int:
        """Get total number of embeddings in store.

        Returns:
            Count of embeddings
        """
        if not self.is_available():
            return 0

        try:
            return self.collection.count()
        except Exception:
            return 0


# Global vector store instance
vector_store = VectorStore()
