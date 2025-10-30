"""ActivityMatcher service - Automatic screenshot-to-TODO matching engine."""

import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
from loguru import logger

from todolist.backend import database as todo_db


class ActivityMatcher:
    """Service for matching screenshots to TODOs using semantic similarity."""

    def __init__(self, db_connection: sqlite3.Connection, similarity_threshold: float = 0.7):
        """Initialize ActivityMatcher.

        Args:
            db_connection: SQLite database connection
            similarity_threshold: Minimum similarity score for matching (0-1)
        """
        self.conn = db_connection
        self.similarity_threshold = similarity_threshold
        self.embedding_service = None
        self.vector_store = None
        self._init_services()

    def _init_services(self):
        """Initialize embedding service and vector store."""
        try:
            from backend.utils.embedding_utils import embedding_service
            if embedding_service.is_available():
                self.embedding_service = embedding_service
                logger.debug("ActivityMatcher: Embedding service initialized")
        except ImportError:
            logger.warning("ActivityMatcher: Embedding service not available")

        try:
            from backend.vector_store import vector_store
            if vector_store.is_available():
                self.vector_store = vector_store
                logger.debug("ActivityMatcher: Vector store initialized")
        except ImportError:
            logger.warning("ActivityMatcher: Vector store not available")

    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings.

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Similarity score (0-1)
        """
        try:
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = float(dot_product / (norm1 * norm2))
            # Ensure in [0, 1] range
            return max(0.0, min(1.0, similarity))

        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    def match_screenshot_to_todos(self, screenshot_id: int) -> List[Dict]:
        """Match a screenshot to relevant TODOs using semantic similarity.

        Args:
            screenshot_id: Screenshot ID to match

        Returns:
            List of matches with confidence scores:
            [{'todo_id': int, 'confidence': float, 'method': str}, ...]
        """
        matches = []

        try:
            # Get screenshot information
            from backend.database import db
            screenshot = db.get_screenshot(screenshot_id)

            if not screenshot or not screenshot.description:
                logger.debug(f"Screenshot {screenshot_id} has no description, skipping matching")
                return []

            # Get screenshot embedding (from vector store or generate)
            screenshot_emb = self._get_screenshot_embedding(screenshot_id, screenshot.description)

            if screenshot_emb is None:
                logger.warning(f"Could not get embedding for screenshot {screenshot_id}")
                return []

            # Get all active TODOs with embeddings
            active_todos = todo_db.get_active_todos(self.conn)

            if not active_todos:
                logger.debug("No active TODOs to match against")
                return []

            # Calculate similarity with each TODO
            for todo in active_todos:
                if todo.get('embedding') is None:
                    continue

                try:
                    # Deserialize TODO embedding
                    todo_emb = np.frombuffer(todo['embedding'], dtype=np.float32)

                    # Calculate similarity
                    similarity = self.cosine_similarity(screenshot_emb, todo_emb)

                    # If above threshold, add to matches
                    if similarity >= self.similarity_threshold:
                        matches.append({
                            'todo_id': todo['id'],
                            'todo_title': todo['title'],
                            'confidence': float(similarity),
                            'method': 'semantic'
                        })
                        logger.debug(
                            f"Match found: Screenshot {screenshot_id} → TODO {todo['id']} "
                            f"(confidence: {similarity:.2f})"
                        )

                except Exception as e:
                    logger.error(f"Error matching TODO {todo['id']}: {e}")
                    continue

            # Sort by confidence (descending)
            matches.sort(key=lambda x: x['confidence'], reverse=True)

            logger.info(f"Screenshot {screenshot_id}: Found {len(matches)} matches")

        except Exception as e:
            logger.error(f"Error in match_screenshot_to_todos for screenshot {screenshot_id}: {e}")

        return matches

    def _get_screenshot_embedding(self, screenshot_id: int, description: str) -> Optional[np.ndarray]:
        """Get or generate embedding for a screenshot.

        Args:
            screenshot_id: Screenshot ID
            description: Screenshot description

        Returns:
            Embedding vector or None
        """
        # Try to get from vector store first
        if self.vector_store:
            try:
                vector_data = self.vector_store.get_by_id(screenshot_id)
                if vector_data and 'embedding' in vector_data:
                    embedding = vector_data['embedding']
                    if isinstance(embedding, list):
                        return np.array(embedding, dtype=np.float32)
                    return embedding
            except Exception as e:
                logger.debug(f"Could not get embedding from vector store: {e}")

        # Generate new embedding
        if self.embedding_service:
            try:
                embedding = self.embedding_service.generate_embedding(description)
                if embedding is not None:
                    logger.debug(f"Generated embedding for screenshot {screenshot_id}")
                    return embedding
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")

        return None

    def create_activity_link(
        self,
        todo_id: int,
        screenshot_id: int,
        confidence: float,
        method: str = "semantic"
    ) -> Optional[int]:
        """Create a TODO activity link.

        Args:
            todo_id: TODO ID
            screenshot_id: Screenshot ID
            confidence: Match confidence score
            method: Match method (semantic/manual/keyword)

        Returns:
            Activity ID or None if failed
        """
        try:
            # Get screenshot for details
            from backend.database import db
            screenshot = db.get_screenshot(screenshot_id)

            if not screenshot:
                logger.error(f"Screenshot {screenshot_id} not found")
                return None

            # Estimate duration
            duration = self.estimate_duration(screenshot_id)

            # Classify activity type
            activity_type = self.classify_activity_type(screenshot.description or "")

            # Create activity link
            activity_id = todo_db.create_todo_activity(
                conn=self.conn,
                todo_id=todo_id,
                screenshot_id=screenshot_id,
                activity_description=screenshot.description,
                match_confidence=confidence,
                match_method=method,
                duration_minutes=duration,
                activity_type=activity_type
            )

            logger.info(
                f"Created activity link: Screenshot {screenshot_id} → TODO {todo_id} "
                f"(confidence: {confidence:.2f}, duration: {duration}min, type: {activity_type})"
            )

            return activity_id

        except Exception as e:
            logger.error(f"Error creating activity link: {e}")
            return None

    def estimate_duration(self, screenshot_id: int) -> int:
        """Estimate activity duration based on surrounding screenshots.

        Args:
            screenshot_id: Screenshot ID

        Returns:
            Estimated duration in minutes
        """
        try:
            from backend.database import db

            # Get this screenshot
            screenshot = db.get_screenshot(screenshot_id)
            if not screenshot:
                return 5  # Default

            # Get surrounding screenshots (±10 minutes)
            time_window = timedelta(minutes=10)
            start_time = screenshot.timestamp - time_window
            end_time = screenshot.timestamp + time_window

            nearby_screenshots = db.get_screenshots(
                start_date=start_time,
                end_date=end_time,
                limit=10
            )

            if len(nearby_screenshots) <= 1:
                return 5  # Default for isolated screenshot

            # Find adjacent screenshots
            prev_screenshot = None
            next_screenshot = None

            for s in nearby_screenshots:
                if s.timestamp < screenshot.timestamp and (prev_screenshot is None or s.timestamp > prev_screenshot.timestamp):
                    prev_screenshot = s
                elif s.timestamp > screenshot.timestamp and (next_screenshot is None or s.timestamp < next_screenshot.timestamp):
                    next_screenshot = s

            # Calculate duration based on gaps
            durations = []

            if prev_screenshot:
                gap = (screenshot.timestamp - prev_screenshot.timestamp).total_seconds() / 60
                if gap < 10:  # Continuous activity
                    durations.append(gap)

            if next_screenshot:
                gap = (next_screenshot.timestamp - screenshot.timestamp).total_seconds() / 60
                if gap < 10:  # Continuous activity
                    durations.append(gap)

            if durations:
                avg_duration = int(sum(durations) / len(durations))
                # Cap at reasonable values
                return min(max(avg_duration, 1), 60)

            return 5  # Default

        except Exception as e:
            logger.error(f"Error estimating duration: {e}")
            return 5

    def classify_activity_type(self, description: str) -> str:
        """Classify activity type based on description.

        Args:
            description: Screenshot description

        Returns:
            Activity type: reading/coding/video/browsing/general
        """
        if not description:
            return "general"

        description_lower = description.lower()

        # Keyword-based classification
        if any(kw in description_lower for kw in ["code", "ide", "editor", "vscode", "vim", "编程", "代码"]):
            return "coding"
        elif any(kw in description_lower for kw in ["youtube", "video", "play", "视频", "播放"]):
            return "video"
        elif any(kw in description_lower for kw in ["pdf", "doc", "article", "read", "阅读", "文档"]):
            return "reading"
        elif any(kw in description_lower for kw in ["browser", "chrome", "firefox", "search", "浏览", "搜索"]):
            return "browsing"
        elif any(kw in description_lower for kw in ["chat", "mail", "slack", "聊天", "邮件"]):
            return "communication"
        else:
            return "general"


# ===== Async Trigger Function =====

def trigger_async_match(screenshot_id: int):
    """Asynchronously trigger activity matching for a screenshot.

    This function is called from backend/capture.py after screenshot analysis.
    It runs in a background thread to avoid blocking the screenshot capture process.

    Args:
        screenshot_id: Screenshot ID to match
    """

    def _match_worker(sid: int):
        """Background worker for activity matching."""
        try:
            from backend.database import db
            conn = db._get_connection()

            matcher = ActivityMatcher(conn)

            # Find matches
            matches = matcher.match_screenshot_to_todos(sid)

            # Create activity links for all matches
            for match in matches:
                matcher.create_activity_link(
                    todo_id=match['todo_id'],
                    screenshot_id=sid,
                    confidence=match['confidence'],
                    method=match['method']
                )

            if matches:
                logger.info(
                    f"Auto-matched screenshot {sid} to {len(matches)} TODO(s): "
                    f"{[m['todo_id'] for m in matches]}"
                )

            conn.close()

        except Exception as e:
            logger.error(f"Activity matching failed for screenshot {sid}: {e}", exc_info=True)

    # Run in background thread
    thread = threading.Thread(target=_match_worker, args=(screenshot_id,), daemon=True)
    thread.start()
    logger.debug(f"Started async matching thread for screenshot {screenshot_id}")
