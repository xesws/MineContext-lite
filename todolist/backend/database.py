"""Database operations for TodoList module."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from loguru import logger


def init_todolist_database(conn: sqlite3.Connection):
    """Initialize TodoList database tables by executing migration scripts.

    Args:
        conn: SQLite database connection from main database

    Raises:
        Exception: If migration fails
    """
    cursor = conn.cursor()
    migrations_dir = Path(__file__).parent.parent / "migrations"

    try:
        # Execute migrations in order
        migration_files = sorted(migrations_dir.glob("*.sql"))

        for migration_file in migration_files:
            logger.info(f"Executing TodoList migration: {migration_file.name}")
            with open(migration_file, "r") as f:
                migration_sql = f.read()
                cursor.executescript(migration_sql)

        conn.commit()
        logger.info("TodoList database initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize TodoList database: {e}")
        conn.rollback()
        raise


# ===== UserTodo CRUD Operations =====

def create_user_todo(
    conn: sqlite3.Connection,
    title: str,
    description: Optional[str] = None,
    parent_id: Optional[int] = None,
    status: str = "pending",
    priority: str = "medium",
    tags: Optional[str] = None,
    due_date: Optional[datetime] = None,
    estimated_hours: Optional[float] = None,
    embedding: Optional[np.ndarray] = None
) -> int:
    """Create a new TODO item.

    Args:
        conn: Database connection
        title: TODO title
        description: Detailed description
        parent_id: Parent TODO ID for subtasks
        status: TODO status
        priority: Priority level
        tags: Comma-separated tags
        due_date: Due date
        estimated_hours: Estimated hours to complete
        embedding: Embedding vector (numpy array)

    Returns:
        Created TODO ID
    """
    cursor = conn.cursor()

    # Serialize embedding if provided
    embedding_blob = embedding.tobytes() if embedding is not None else None
    due_date_str = due_date.isoformat() if due_date else None

    cursor.execute(
        """
        INSERT INTO user_todos (
            title, description, parent_id, status, priority,
            tags, due_date, estimated_hours, embedding
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title, description, parent_id, status, priority,
            tags, due_date_str, estimated_hours, embedding_blob
        )
    )
    conn.commit()

    return cursor.lastrowid


def get_user_todo(conn: sqlite3.Connection, todo_id: int) -> Optional[Dict]:
    """Get a single TODO by ID.

    Args:
        conn: Database connection
        todo_id: TODO ID

    Returns:
        TODO dictionary or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()

    if row:
        return _row_to_dict(row)
    return None


def get_user_todos(
    conn: sqlite3.Connection,
    status: Optional[str] = None,
    parent_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """Get list of TODOs with optional filters.

    Args:
        conn: Database connection
        status: Filter by status (optional)
        parent_id: Filter by parent_id (optional, use -1 for root TODOs)
        limit: Maximum results
        offset: Pagination offset

    Returns:
        List of TODO dictionaries
    """
    cursor = conn.cursor()

    query = "SELECT * FROM user_todos WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if parent_id is not None:
        if parent_id == -1:
            # Get root TODOs (no parent)
            query += " AND parent_id IS NULL"
        else:
            query += " AND parent_id = ?"
            params.append(parent_id)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()

    return [_row_to_dict(row) for row in rows]


def get_active_todos(conn: sqlite3.Connection) -> List[Dict]:
    """Get all active TODOs (pending or in_progress) for activity matching.

    Args:
        conn: Database connection

    Returns:
        List of active TODO dictionaries with embeddings
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM user_todos
        WHERE status IN ('pending', 'in_progress')
        AND embedding IS NOT NULL
        ORDER BY updated_at DESC
        """
    )
    rows = cursor.fetchall()

    return [_row_to_dict(row) for row in rows]


def get_todo_tree(conn: sqlite3.Connection) -> List[Dict]:
    """Get TODO tree structure (root TODOs with nested children).

    Returns:
        List of root TODO dictionaries with 'children' field
    """

    def _get_children(parent_id: int) -> List[Dict]:
        """Recursively get children of a TODO."""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM user_todos WHERE parent_id = ? ORDER BY created_at",
            (parent_id,)
        )
        children = [_row_to_dict(row) for row in cursor.fetchall()]

        for child in children:
            child['children'] = _get_children(child['id'])

        return children

    # Get root TODOs (no parent)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM user_todos WHERE parent_id IS NULL ORDER BY created_at"
    )
    root_todos = [_row_to_dict(row) for row in cursor.fetchall()]

    # Get children for each root TODO
    for todo in root_todos:
        todo['children'] = _get_children(todo['id'])

    return root_todos


def update_user_todo(
    conn: sqlite3.Connection,
    todo_id: int,
    **kwargs
) -> bool:
    """Update a TODO item.

    Args:
        conn: Database connection
        todo_id: TODO ID
        **kwargs: Fields to update (title, description, status, priority, tags,
                  due_date, estimated_hours, completion_percentage, embedding)

    Returns:
        True if successful
    """
    if not kwargs:
        return False

    # Handle special conversions
    if 'due_date' in kwargs and kwargs['due_date']:
        kwargs['due_date'] = kwargs['due_date'].isoformat()

    if 'embedding' in kwargs and kwargs['embedding'] is not None:
        kwargs['embedding'] = kwargs['embedding'].tobytes()

    # Always update updated_at
    kwargs['updated_at'] = datetime.now().isoformat()

    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values()) + [todo_id]

    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE user_todos SET {set_clause} WHERE id = ?",
        values
    )
    conn.commit()

    return cursor.rowcount > 0


def delete_user_todo(conn: sqlite3.Connection, todo_id: int) -> bool:
    """Delete a TODO (cascading delete of children and activities).

    Args:
        conn: Database connection
        todo_id: TODO ID

    Returns:
        True if successful
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_todos WHERE id = ?", (todo_id,))
    conn.commit()

    return cursor.rowcount > 0


def get_todo_count(conn: sqlite3.Connection, status: Optional[str] = None) -> int:
    """Get count of TODOs by status.

    Args:
        conn: Database connection
        status: Filter by status (optional)

    Returns:
        TODO count
    """
    cursor = conn.cursor()

    if status:
        cursor.execute("SELECT COUNT(*) FROM user_todos WHERE status = ?", (status,))
    else:
        cursor.execute("SELECT COUNT(*) FROM user_todos")

    return cursor.fetchone()[0]


# ===== TodoActivity CRUD Operations =====

def create_todo_activity(
    conn: sqlite3.Connection,
    todo_id: int,
    screenshot_id: int,
    activity_description: Optional[str] = None,
    match_confidence: Optional[float] = None,
    match_method: str = "semantic",
    duration_minutes: Optional[int] = None,
    activity_type: Optional[str] = None
) -> int:
    """Create a TODO activity link.

    Args:
        conn: Database connection
        todo_id: TODO ID
        screenshot_id: Screenshot ID
        activity_description: Activity description
        match_confidence: Confidence score (0-1)
        match_method: Match method (semantic/keyword/manual)
        duration_minutes: Activity duration
        activity_type: Activity type

    Returns:
        Created activity ID
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO todo_activities (
            todo_id, screenshot_id, activity_description,
            match_confidence, match_method, duration_minutes, activity_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            todo_id, screenshot_id, activity_description,
            match_confidence, match_method, duration_minutes, activity_type
        )
    )
    conn.commit()

    return cursor.lastrowid


def get_todo_activities(
    conn: sqlite3.Connection,
    todo_id: int,
    limit: Optional[int] = None
) -> List[Dict]:
    """Get all activities for a TODO.

    Args:
        conn: Database connection
        todo_id: TODO ID
        limit: Maximum results (optional)

    Returns:
        List of activity dictionaries
    """
    cursor = conn.cursor()

    query = """
        SELECT a.*, s.timestamp as screenshot_timestamp, s.description as screenshot_description,
               s.filepath as screenshot_filepath
        FROM todo_activities a
        LEFT JOIN screenshots s ON a.screenshot_id = s.id
        WHERE a.todo_id = ?
        ORDER BY a.matched_at DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query, (todo_id,))
    rows = cursor.fetchall()

    return [_row_to_dict(row) for row in rows]


def get_activities_by_screenshot(
    conn: sqlite3.Connection,
    screenshot_id: int
) -> List[Dict]:
    """Get all TODO activities for a screenshot.

    Args:
        conn: Database connection
        screenshot_id: Screenshot ID

    Returns:
        List of activity dictionaries
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.*, t.title as todo_title, t.status as todo_status
        FROM todo_activities a
        LEFT JOIN user_todos t ON a.todo_id = t.id
        WHERE a.screenshot_id = ?
        ORDER BY a.matched_at DESC
        """,
        (screenshot_id,)
    )
    rows = cursor.fetchall()

    return [_row_to_dict(row) for row in rows]


def delete_todo_activity(conn: sqlite3.Connection, activity_id: int) -> bool:
    """Delete a TODO activity link.

    Args:
        conn: Database connection
        activity_id: Activity ID

    Returns:
        True if successful
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todo_activities WHERE id = ?", (activity_id,))
    conn.commit()

    return cursor.rowcount > 0


def calculate_total_time_spent(conn: sqlite3.Connection, todo_id: int) -> int:
    """Calculate total time spent on a TODO (sum of activity durations).

    Args:
        conn: Database connection
        todo_id: TODO ID

    Returns:
        Total time in minutes
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COALESCE(SUM(duration_minutes), 0)
        FROM todo_activities
        WHERE todo_id = ?
        """,
        (todo_id,)
    )

    return cursor.fetchone()[0]


# ===== TodoProgressSnapshot CRUD Operations =====

def create_progress_snapshot(
    conn: sqlite3.Connection,
    todo_id: int,
    completed_aspects: List[str],
    remaining_aspects: List[str],
    total_time_spent: int,
    ai_summary: str,
    completion_percentage: int,
    next_steps: List[str]
) -> int:
    """Create a progress snapshot.

    Args:
        conn: Database connection
        todo_id: TODO ID
        completed_aspects: List of completed items
        remaining_aspects: List of remaining items
        total_time_spent: Total time in minutes
        ai_summary: AI-generated summary
        completion_percentage: Completion percentage (0-100)
        next_steps: List of recommended next steps

    Returns:
        Created snapshot ID
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO todo_progress_snapshots (
            todo_id, completed_aspects, remaining_aspects,
            total_time_spent, ai_summary, completion_percentage, next_steps
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            todo_id,
            json.dumps(completed_aspects),
            json.dumps(remaining_aspects),
            total_time_spent,
            ai_summary,
            completion_percentage,
            json.dumps(next_steps)
        )
    )
    conn.commit()

    return cursor.lastrowid


def get_latest_progress_snapshot(
    conn: sqlite3.Connection,
    todo_id: int
) -> Optional[Dict]:
    """Get the most recent progress snapshot for a TODO.

    Args:
        conn: Database connection
        todo_id: TODO ID

    Returns:
        Snapshot dictionary or None
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM todo_progress_snapshots
        WHERE todo_id = ?
        ORDER BY analyzed_at DESC
        LIMIT 1
        """,
        (todo_id,)
    )
    row = cursor.fetchone()

    if row:
        return _row_to_dict(row)
    return None


def get_progress_snapshots(
    conn: sqlite3.Connection,
    todo_id: int,
    limit: int = 10
) -> List[Dict]:
    """Get progress snapshot history for a TODO.

    Args:
        conn: Database connection
        todo_id: TODO ID
        limit: Maximum results

    Returns:
        List of snapshot dictionaries
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM todo_progress_snapshots
        WHERE todo_id = ?
        ORDER BY analyzed_at DESC
        LIMIT ?
        """,
        (todo_id, limit)
    )
    rows = cursor.fetchall()

    return [_row_to_dict(row) for row in rows]


# ===== Statistics =====

def get_todo_stats(conn: sqlite3.Connection) -> Dict:
    """Get TODO statistics.

    Args:
        conn: Database connection

    Returns:
        Statistics dictionary
    """
    cursor = conn.cursor()

    # Total TODOs
    cursor.execute("SELECT COUNT(*) FROM user_todos")
    total = cursor.fetchone()[0]

    # By status
    cursor.execute("SELECT COUNT(*) FROM user_todos WHERE status = 'pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_todos WHERE status = 'in_progress'")
    in_progress = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_todos WHERE status = 'completed'")
    completed = cursor.fetchone()[0]

    # Overdue TODOs
    cursor.execute(
        """
        SELECT COUNT(*) FROM user_todos
        WHERE due_date < ? AND status NOT IN ('completed', 'archived')
        """,
        (datetime.now().isoformat(),)
    )
    overdue = cursor.fetchone()[0]

    # Total activities
    cursor.execute("SELECT COUNT(*) FROM todo_activities")
    total_activities = cursor.fetchone()[0]

    return {
        "total_todos": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "overdue": overdue,
        "total_activities": total_activities
    }


# ===== Utility Functions =====

def _row_to_dict(row: sqlite3.Row) -> Dict:
    """Convert SQLite row to dictionary.

    Args:
        row: SQLite row object

    Returns:
        Dictionary with row data
    """
    return dict(row)
