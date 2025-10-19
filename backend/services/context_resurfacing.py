"""Context resurfacing service for proactive context delivery."""

from datetime import datetime, timedelta
from typing import List, Optional

from loguru import logger

from backend.config import settings
from backend.database import db
from backend.models import SimilarScreenshot
from backend.utils.embedding_utils import embedding_service
from backend.vector_store import vector_store


class ContextResurfacingService:
    """Service for proactively resurfacing relevant contexts."""

    def __init__(self):
        """Initialize context resurfacing service."""
        self.enabled = settings.context_resurfacing.enabled

    def is_available(self) -> bool:
        """Check if context resurfacing is available.

        Returns:
            True if service is enabled and dependencies are available
        """
        return (
            self.enabled
            and embedding_service.is_available()
            and vector_store.is_available()
        )

    def find_related_contexts(
        self,
        screenshot_id: int,
        max_results: Optional[int] = None
    ) -> List[SimilarScreenshot]:
        """Find contexts related to a specific screenshot.

        Args:
            screenshot_id: Screenshot ID to find related contexts for
            max_results: Maximum number of results

        Returns:
            List of similar screenshots
        """
        if not self.is_available():
            logger.warning("Context resurfacing service not available")
            return []

        try:
            # Get the screenshot embedding from vector store
            vector_data = vector_store.get_by_id(screenshot_id)
            if not vector_data:
                logger.warning(f"No embedding found for screenshot {screenshot_id}")
                return []

            embedding = vector_data['embedding']

            # Search for similar contexts
            max_results = max_results or settings.context_resurfacing.max_suggestions
            min_similarity = settings.context_resurfacing.min_similarity

            similar_items = vector_store.search_similar(
                query_embedding=embedding,
                top_k=max_results + 1,  # +1 to exclude self
                min_similarity=min_similarity
            )

            # Filter out the screenshot itself
            related = [
                SimilarScreenshot(**item)
                for item in similar_items
                if item['screenshot_id'] != screenshot_id
            ]

            # Apply relevance decay based on time
            related = self._apply_relevance_decay(related)

            return related[:max_results]

        except Exception as e:
            logger.error(f"Error finding related contexts for screenshot {screenshot_id}: {e}")
            return []

    def resurface_by_query(
        self,
        query_text: str,
        max_results: Optional[int] = None,
        time_window_days: Optional[int] = None
    ) -> List[SimilarScreenshot]:
        """Resurface contexts based on a text query.

        Args:
            query_text: Text query for finding relevant contexts
            max_results: Maximum number of results
            time_window_days: Only include contexts from last N days

        Returns:
            List of relevant contexts
        """
        if not self.is_available():
            logger.warning("Context resurfacing service not available")
            return []

        try:
            max_results = max_results or settings.context_resurfacing.max_suggestions
            min_similarity = settings.context_resurfacing.min_similarity

            # Search for similar contexts by text
            results = vector_store.search_by_text(
                query_text=query_text,
                top_k=max_results * 2,  # Get more to filter by time
                min_similarity=min_similarity
            )

            # Convert to SimilarScreenshot objects
            similar = [SimilarScreenshot(**item) for item in results]

            # Filter by time window if specified
            if time_window_days:
                cutoff_date = datetime.now() - timedelta(days=time_window_days)
                similar = [
                    s for s in similar
                    if s.timestamp and datetime.fromisoformat(s.timestamp) >= cutoff_date
                ]

            # Apply relevance decay
            similar = self._apply_relevance_decay(similar)

            return similar[:max_results]

        except Exception as e:
            logger.error(f"Error resurfacing contexts for query '{query_text}': {e}")
            return []

    def get_proactive_suggestions(
        self,
        current_context: Optional[str] = None,
        max_suggestions: Optional[int] = None
    ) -> List[SimilarScreenshot]:
        """Get proactive context suggestions.

        Args:
            current_context: Current activity or context description
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested contexts
        """
        if not self.is_available():
            return []

        max_suggestions = max_suggestions or settings.context_resurfacing.max_suggestions

        if current_context:
            # Use the current context to find relevant historical contexts
            return self.resurface_by_query(current_context, max_suggestions)
        else:
            # Get recent contexts as fallback
            return self._get_recent_diverse_contexts(max_suggestions)

    def _apply_relevance_decay(
        self,
        screenshots: List[SimilarScreenshot]
    ) -> List[SimilarScreenshot]:
        """Apply time-based relevance decay to similarity scores.

        More recent contexts are more relevant. Apply exponential decay.

        Args:
            screenshots: List of similar screenshots

        Returns:
            List with adjusted similarity scores
        """
        decay_days = settings.context_resurfacing.relevance_decay_days
        now = datetime.now()

        for screenshot in screenshots:
            if screenshot.timestamp:
                try:
                    timestamp = datetime.fromisoformat(screenshot.timestamp)
                    age_days = (now - timestamp).days

                    # Exponential decay: score = original_score * exp(-age/decay_period)
                    # This gives ~37% weight at decay_days, ~14% at 2*decay_days
                    import math
                    decay_factor = math.exp(-age_days / decay_days)

                    # Adjust similarity score
                    screenshot.similarity *= decay_factor

                except Exception as e:
                    logger.warning(f"Error applying relevance decay: {e}")
                    continue

        # Re-sort by adjusted similarity
        screenshots.sort(key=lambda x: x.similarity, reverse=True)

        return screenshots

    def _get_recent_diverse_contexts(
        self,
        max_results: int
    ) -> List[SimilarScreenshot]:
        """Get recent diverse contexts when no specific query is provided.

        Args:
            max_results: Maximum number of results

        Returns:
            List of diverse recent contexts
        """
        try:
            # Get recent screenshots
            recent = db.get_screenshots(limit=max_results * 2)

            # Convert to SimilarScreenshot format with default similarity
            suggestions = []
            for screenshot in recent:
                if screenshot.analyzed and screenshot.embedding_generated:
                    suggestions.append(SimilarScreenshot(
                        screenshot_id=screenshot.id,
                        similarity=0.8,  # Default high relevance for recent items
                        description=screenshot.description,
                        tags=screenshot.tags,
                        timestamp=screenshot.timestamp.isoformat()
                    ))

            return suggestions[:max_results]

        except Exception as e:
            logger.error(f"Error getting recent diverse contexts: {e}")
            return []

    def find_context_gaps(
        self,
        time_window_hours: int = 24
    ) -> List[dict]:
        """Identify gaps in context coverage (periods with no activity).

        Args:
            time_window_hours: Time window to analyze

        Returns:
            List of time gaps
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

            # Get screenshots in time window
            screenshots = db.get_screenshots(
                start_date=cutoff_time,
                limit=1000
            )

            if len(screenshots) < 2:
                return []

            # Find gaps (periods with no screenshots)
            gaps = []
            for i in range(len(screenshots) - 1):
                current = screenshots[i]
                next_shot = screenshots[i + 1]

                gap_minutes = (current.timestamp - next_shot.timestamp).total_seconds() / 60

                # Consider gaps > 30 minutes significant
                if gap_minutes > 30:
                    gaps.append({
                        "start": next_shot.timestamp.isoformat(),
                        "end": current.timestamp.isoformat(),
                        "duration_minutes": gap_minutes
                    })

            return gaps

        except Exception as e:
            logger.error(f"Error finding context gaps: {e}")
            return []


# Global context resurfacing service instance
context_resurfacing_service = ContextResurfacingService()
