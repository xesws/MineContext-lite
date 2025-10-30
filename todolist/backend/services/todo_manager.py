"""TodoManager service - Core business logic for TODO operations."""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
from loguru import logger

from todolist.backend import database as todo_db


class TodoManager:
    """Service for managing TODO items with embedding generation."""

    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize TodoManager.

        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.embedding_service = None
        self._init_embedding_service()

    def _init_embedding_service(self):
        """Initialize embedding service if available."""
        try:
            from backend.utils.embedding_utils import embedding_service
            if embedding_service.is_available():
                self.embedding_service = embedding_service
                logger.info("TodoManager: Embedding service initialized")
            else:
                logger.warning("TodoManager: Embedding service not available")
        except ImportError:
            logger.warning("TodoManager: Could not import embedding service")

    def _generate_embedding(self, title: str, description: Optional[str]) -> Optional[np.ndarray]:
        """Generate embedding for TODO.

        Combines title and description for embedding generation.

        Args:
            title: TODO title
            description: TODO description

        Returns:
            Embedding vector or None if service unavailable
        """
        if not self.embedding_service:
            return None

        # Combine title and description
        text = title
        if description:
            text += f"\n{description}"

        try:
            embedding = self.embedding_service.generate_embedding(text)
            if embedding is not None:
                logger.debug(f"Generated embedding for TODO: {title[:50]}...")
                return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")

        return None

    def create_todo(
        self,
        title: str,
        description: Optional[str] = None,
        parent_id: Optional[int] = None,
        priority: str = "medium",
        tags: Optional[str] = None,
        due_date: Optional[datetime] = None,
        estimated_hours: Optional[float] = None
    ) -> Dict:
        """Create a new TODO with automatic embedding generation.

        Args:
            title: TODO title
            description: Detailed description
            parent_id: Parent TODO ID for subtasks
            priority: Priority level (low/medium/high)
            tags: Comma-separated tags
            due_date: Due date
            estimated_hours: Estimated hours to complete

        Returns:
            Created TODO dictionary

        Raises:
            ValueError: If parent_id doesn't exist
        """
        # Validate parent_id if provided
        if parent_id is not None:
            parent = todo_db.get_user_todo(self.conn, parent_id)
            if not parent:
                raise ValueError(f"Parent TODO with ID {parent_id} not found")

        # Generate embedding
        embedding = self._generate_embedding(title, description)

        # Create TODO
        todo_id = todo_db.create_user_todo(
            conn=self.conn,
            title=title,
            description=description,
            parent_id=parent_id,
            status="pending",
            priority=priority,
            tags=tags,
            due_date=due_date,
            estimated_hours=estimated_hours,
            embedding=embedding
        )

        logger.info(f"Created TODO {todo_id}: {title}")

        # Return created TODO
        todo = todo_db.get_user_todo(self.conn, todo_id)
        return todo

    def get_todo(self, todo_id: int) -> Optional[Dict]:
        """Get a single TODO by ID.

        Args:
            todo_id: TODO ID

        Returns:
            TODO dictionary or None
        """
        return todo_db.get_user_todo(self.conn, todo_id)

    def get_todos(
        self,
        status: Optional[str] = None,
        parent_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Get list of TODOs with optional filters.

        Args:
            status: Filter by status
            parent_id: Filter by parent_id (-1 for root TODOs)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of TODO dictionaries
        """
        return todo_db.get_user_todos(
            conn=self.conn,
            status=status,
            parent_id=parent_id,
            limit=limit,
            offset=offset
        )

    def get_todo_tree(self) -> List[Dict]:
        """Get TODO tree structure (hierarchical).

        Returns:
            List of root TODOs with nested children
        """
        return todo_db.get_todo_tree(self.conn)

    def get_active_todos(self) -> List[Dict]:
        """Get all active TODOs for activity matching.

        Returns:
            List of active TODO dictionaries with embeddings
        """
        return todo_db.get_active_todos(self.conn)

    def update_todo(
        self,
        todo_id: int,
        **kwargs
    ) -> Optional[Dict]:
        """Update a TODO.

        If description is updated, regenerates embedding.

        Args:
            todo_id: TODO ID
            **kwargs: Fields to update

        Returns:
            Updated TODO dictionary or None if not found

        Raises:
            ValueError: If TODO not found
        """
        # Check if TODO exists
        todo = todo_db.get_user_todo(self.conn, todo_id)
        if not todo:
            raise ValueError(f"TODO with ID {todo_id} not found")

        # If description or title changed, regenerate embedding
        if 'description' in kwargs or 'title' in kwargs:
            new_title = kwargs.get('title', todo['title'])
            new_description = kwargs.get('description', todo['description'])

            embedding = self._generate_embedding(new_title, new_description)
            if embedding is not None:
                kwargs['embedding'] = embedding

        # Update TODO
        success = todo_db.update_user_todo(self.conn, todo_id, **kwargs)

        if success:
            logger.info(f"Updated TODO {todo_id}")
            return todo_db.get_user_todo(self.conn, todo_id)

        return None

    def delete_todo(self, todo_id: int) -> bool:
        """Delete a TODO (cascading delete of children and activities).

        Args:
            todo_id: TODO ID

        Returns:
            True if successful

        Raises:
            ValueError: If TODO not found
        """
        # Check if TODO exists
        todo = todo_db.get_user_todo(self.conn, todo_id)
        if not todo:
            raise ValueError(f"TODO with ID {todo_id} not found")

        success = todo_db.delete_user_todo(self.conn, todo_id)

        if success:
            logger.info(f"Deleted TODO {todo_id}: {todo['title']}")

        return success

    def get_todo_with_details(self, todo_id: int) -> Optional[Dict]:
        """Get TODO with activities and progress information.

        Args:
            todo_id: TODO ID

        Returns:
            Detailed TODO dictionary with activities and progress
        """
        todo = todo_db.get_user_todo(self.conn, todo_id)
        if not todo:
            return None

        # Get children
        children = todo_db.get_user_todos(self.conn, parent_id=todo_id, limit=1000)

        # Get activities
        activities = todo_db.get_todo_activities(self.conn, todo_id)

        # Get latest progress
        latest_progress = todo_db.get_latest_progress_snapshot(self.conn, todo_id)

        # Calculate total time spent
        total_time = todo_db.calculate_total_time_spent(self.conn, todo_id)

        # Build detailed response
        todo['children'] = children
        todo['activities'] = activities
        todo['latest_progress'] = latest_progress
        todo['total_time_spent'] = total_time
        todo['activities_count'] = len(activities)

        return todo

    def get_todo_activities(self, todo_id: int, limit: Optional[int] = None) -> List[Dict]:
        """Get activity timeline for a TODO.

        Args:
            todo_id: TODO ID
            limit: Maximum results

        Returns:
            List of activity dictionaries
        """
        return todo_db.get_todo_activities(self.conn, todo_id, limit=limit)

    def link_activity(
        self,
        todo_id: int,
        screenshot_id: int,
        activity_description: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        match_method: str = "manual",
        match_confidence: Optional[float] = None
    ) -> int:
        """Manually link a screenshot to a TODO.

        Args:
            todo_id: TODO ID
            screenshot_id: Screenshot ID
            activity_description: Activity description
            duration_minutes: Activity duration
            match_method: Match method (default: manual)
            match_confidence: Confidence score

        Returns:
            Created activity ID

        Raises:
            ValueError: If TODO doesn't exist
        """
        # Verify TODO exists
        todo = todo_db.get_user_todo(self.conn, todo_id)
        if not todo:
            raise ValueError(f"TODO with ID {todo_id} not found")

        # Create activity link
        activity_id = todo_db.create_todo_activity(
            conn=self.conn,
            todo_id=todo_id,
            screenshot_id=screenshot_id,
            activity_description=activity_description,
            match_confidence=match_confidence,
            match_method=match_method,
            duration_minutes=duration_minutes
        )

        logger.info(f"Linked screenshot {screenshot_id} to TODO {todo_id} (activity {activity_id})")

        return activity_id

    def unlink_activity(self, activity_id: int) -> bool:
        """Delete an activity link.

        Args:
            activity_id: Activity ID

        Returns:
            True if successful
        """
        success = todo_db.delete_todo_activity(self.conn, activity_id)

        if success:
            logger.info(f"Deleted activity {activity_id}")

        return success

    def get_stats(self) -> Dict:
        """Get TODO statistics.

        Returns:
            Statistics dictionary
        """
        return todo_db.get_todo_stats(self.conn)


# Factory function to create TodoManager instance
def get_todo_manager() -> TodoManager:
    """Get TodoManager instance with database connection.

    Returns:
        TodoManager instance
    """
    from backend.database import db
    conn = db._get_connection()
    return TodoManager(conn)
