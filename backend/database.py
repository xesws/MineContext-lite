"""Database operations for MineContext-v2."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from backend.config import settings
from backend.models import (
    Activity,
    ActivityCreate,
    Screenshot,
    ScreenshotCreate,
    ScreenshotUpdate,
)


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or settings.storage.database_path
        self._ensure_db_exists()
        self._init_schema()

    def _ensure_db_exists(self):
        """Ensure database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection.

        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create screenshots table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    image_hash TEXT,
                    description TEXT,
                    tags TEXT,
                    app_name TEXT,
                    window_title TEXT,
                    analyzed BOOLEAN DEFAULT 0,
                    file_size INTEGER,
                    embedding_generated BOOLEAN DEFAULT 0,
                    embedding_model TEXT,
                    embedding_generated_at DATETIME,
                    session_id INTEGER,
                    productivity_score FLOAT
                )
                """
            )

            # Create activities table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    screenshot_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    duration_seconds INTEGER DEFAULT 0,
                    app_category TEXT,
                    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE CASCADE
                )
                """
            )

            # Create work_sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS work_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    duration_seconds INTEGER DEFAULT 0,
                    activity_count INTEGER DEFAULT 0,
                    dominant_activity TEXT,
                    productivity_score FLOAT DEFAULT 0.0,
                    notes TEXT
                )
                """
            )

            # Create activity_summaries table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    activity_type TEXT NOT NULL,
                    total_seconds INTEGER DEFAULT 0,
                    screenshot_count INTEGER DEFAULT 0,
                    app_breakdown TEXT,
                    UNIQUE(date, activity_type)
                )
                """
            )

            # Create generated_reports table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS generated_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    period_start DATE NOT NULL,
                    period_end DATE NOT NULL,
                    content TEXT NOT NULL,
                    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
                """
            )

            # Create extracted_todos table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS extracted_todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    screenshot_id INTEGER,
                    todo_text TEXT NOT NULL,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE CASCADE
                )
                """
            )

            conn.commit()

            # Run migration to add new columns if they don't exist
            self._migrate_schema(conn)

            # Create indexes for better query performance (after migration)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_screenshots_timestamp ON screenshots(timestamp DESC)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_screenshots_hash ON screenshots(image_hash)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_screenshots_embedding ON screenshots(embedding_generated)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_screenshots_session ON screenshots(session_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_activities_screenshot ON activities(screenshot_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp DESC)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(activity_type)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_work_sessions_time ON work_sessions(start_time DESC)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_activity_summaries_date ON activity_summaries(date DESC)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_reports_type_date ON generated_reports(report_type, period_start DESC)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_todos_status ON extracted_todos(status)"
            )

            conn.commit()

            logger.info(f"Database initialized at {self.db_path}")

    def _migrate_schema(self, conn: sqlite3.Connection):
        """Migrate database schema to add new columns if they don't exist.

        Args:
            conn: Database connection
        """
        cursor = conn.cursor()

        # Check if embedding columns exist in screenshots
        cursor.execute("PRAGMA table_info(screenshots)")
        screenshot_columns = [row[1] for row in cursor.fetchall()]

        # Add embedding-related columns
        if "embedding_generated" not in screenshot_columns:
            logger.info("Adding embedding_generated column to screenshots table")
            cursor.execute("ALTER TABLE screenshots ADD COLUMN embedding_generated BOOLEAN DEFAULT 0")

        if "embedding_model" not in screenshot_columns:
            logger.info("Adding embedding_model column to screenshots table")
            cursor.execute("ALTER TABLE screenshots ADD COLUMN embedding_model TEXT")

        if "embedding_generated_at" not in screenshot_columns:
            logger.info("Adding embedding_generated_at column to screenshots table")
            cursor.execute("ALTER TABLE screenshots ADD COLUMN embedding_generated_at DATETIME")

        # Add Phase 5A columns
        if "session_id" not in screenshot_columns:
            logger.info("Adding session_id column to screenshots table")
            cursor.execute("ALTER TABLE screenshots ADD COLUMN session_id INTEGER")

        if "productivity_score" not in screenshot_columns:
            logger.info("Adding productivity_score column to screenshots table")
            cursor.execute("ALTER TABLE screenshots ADD COLUMN productivity_score FLOAT")

        # Check activities table
        cursor.execute("PRAGMA table_info(activities)")
        activity_columns = [row[1] for row in cursor.fetchall()]

        if "duration_seconds" not in activity_columns:
            logger.info("Adding duration_seconds column to activities table")
            cursor.execute("ALTER TABLE activities ADD COLUMN duration_seconds INTEGER DEFAULT 0")

        if "app_category" not in activity_columns:
            logger.info("Adding app_category column to activities table")
            cursor.execute("ALTER TABLE activities ADD COLUMN app_category TEXT")

        # Check extracted_todos table for new columns
        cursor.execute("PRAGMA table_info(extracted_todos)")
        todos_columns = [row[1] for row in cursor.fetchall()]

        if "due_date" not in todos_columns:
            logger.info("Adding due_date column to extracted_todos table")
            cursor.execute("ALTER TABLE extracted_todos ADD COLUMN due_date DATETIME")

        if "created_by" not in todos_columns:
            logger.info("Adding created_by column to extracted_todos table")
            cursor.execute("ALTER TABLE extracted_todos ADD COLUMN created_by TEXT DEFAULT 'ai_extracted'")

        if "title" not in todos_columns:
            logger.info("Adding title column to extracted_todos table")
            cursor.execute("ALTER TABLE extracted_todos ADD COLUMN title TEXT")

        if "notes" not in todos_columns:
            logger.info("Adding notes column to extracted_todos table")
            cursor.execute("ALTER TABLE extracted_todos ADD COLUMN notes TEXT")

        conn.commit()

    # Screenshot CRUD operations

    def create_screenshot(self, screenshot: ScreenshotCreate) -> Screenshot:
        """Create a new screenshot record.

        Args:
            screenshot: Screenshot data to create

        Returns:
            Created screenshot with ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO screenshots (
                    filepath, image_hash, description, tags,
                    app_name, window_title, file_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    screenshot.filepath,
                    screenshot.image_hash,
                    screenshot.description,
                    screenshot.tags,
                    screenshot.app_name,
                    screenshot.window_title,
                    screenshot.file_size,
                ),
            )
            conn.commit()

            screenshot_id = cursor.lastrowid
            return self.get_screenshot(screenshot_id)

    def get_screenshot(self, screenshot_id: int) -> Optional[Screenshot]:
        """Get screenshot by ID.

        Args:
            screenshot_id: Screenshot ID

        Returns:
            Screenshot if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM screenshots WHERE id = ?", (screenshot_id,))
            row = cursor.fetchone()

            if row:
                return Screenshot(**dict(row))
            return None

    def get_screenshots(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Screenshot]:
        """Get list of screenshots with optional filters.

        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            start_date: Filter screenshots after this date
            end_date: Filter screenshots before this date

        Returns:
            List of screenshots
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM screenshots WHERE 1=1"
            params = []

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [Screenshot(**dict(row)) for row in rows]

    def update_screenshot(
        self, screenshot_id: int, update: ScreenshotUpdate
    ) -> Optional[Screenshot]:
        """Update screenshot.

        Args:
            screenshot_id: Screenshot ID
            update: Fields to update

        Returns:
            Updated screenshot if found, None otherwise
        """
        update_data = update.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_screenshot(screenshot_id)

        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(screenshot_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE screenshots SET {set_clause} WHERE id = ?", values
            )
            conn.commit()

        return self.get_screenshot(screenshot_id)

    def delete_screenshot(self, screenshot_id: int) -> bool:
        """Delete screenshot by ID.

        Args:
            screenshot_id: Screenshot ID

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM screenshots WHERE id = ?", (screenshot_id,))
            conn.commit()
            return cursor.rowcount > 0

    def search_screenshots(
        self, query: str, limit: int = 100, offset: int = 0
    ) -> List[Screenshot]:
        """Search screenshots by description or tags.

        Args:
            query: Search query
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of matching screenshots
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"

            cursor.execute(
                """
                SELECT * FROM screenshots
                WHERE description LIKE ? OR tags LIKE ? OR window_title LIKE ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (search_pattern, search_pattern, search_pattern, limit, offset),
            )
            rows = cursor.fetchall()

            return [Screenshot(**dict(row)) for row in rows]

    def find_duplicate_hash(self, image_hash: str) -> Optional[Screenshot]:
        """Find screenshot with matching hash.

        Args:
            image_hash: Perceptual image hash

        Returns:
            Screenshot if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM screenshots WHERE image_hash = ? ORDER BY timestamp DESC LIMIT 1",
                (image_hash,),
            )
            row = cursor.fetchone()

            if row:
                return Screenshot(**dict(row))
            return None

    # Activity CRUD operations

    def create_activity(self, activity: ActivityCreate) -> Activity:
        """Create a new activity record.

        Args:
            activity: Activity data to create

        Returns:
            Created activity with ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO activities (screenshot_id, activity_type, content)
                VALUES (?, ?, ?)
                """,
                (activity.screenshot_id, activity.activity_type, activity.content),
            )
            conn.commit()

            activity_id = cursor.lastrowid
            return self.get_activity(activity_id)

    def get_activity(self, activity_id: int) -> Optional[Activity]:
        """Get activity by ID.

        Args:
            activity_id: Activity ID

        Returns:
            Activity if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
            row = cursor.fetchone()

            if row:
                return Activity(**dict(row))
            return None

    def get_activities_by_screenshot(self, screenshot_id: int) -> List[Activity]:
        """Get all activities for a screenshot.

        Args:
            screenshot_id: Screenshot ID

        Returns:
            List of activities
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM activities WHERE screenshot_id = ? ORDER BY timestamp DESC",
                (screenshot_id,),
            )
            rows = cursor.fetchall()

            return [Activity(**dict(row)) for row in rows]

    # Utility methods

    def get_total_screenshots(self) -> int:
        """Get total number of screenshots.

        Returns:
            Total screenshot count
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM screenshots")
            return cursor.fetchone()[0]

    def cleanup_old_screenshots(self, max_count: int) -> int:
        """Delete oldest screenshots if exceeding max_count.

        Args:
            max_count: Maximum number of screenshots to keep

        Returns:
            Number of screenshots deleted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get IDs of screenshots to delete
            cursor.execute(
                """
                SELECT id FROM screenshots
                ORDER BY timestamp DESC
                LIMIT -1 OFFSET ?
                """,
                (max_count,),
            )
            ids_to_delete = [row[0] for row in cursor.fetchall()]

            if ids_to_delete:
                placeholders = ",".join("?" * len(ids_to_delete))
                cursor.execute(
                    f"DELETE FROM screenshots WHERE id IN ({placeholders})",
                    ids_to_delete,
                )
                conn.commit()
                logger.info(f"Deleted {len(ids_to_delete)} old screenshots")
                return len(ids_to_delete)

            return 0

    # Embedding management methods

    def get_screenshots_without_embeddings(self, limit: Optional[int] = None) -> List[Screenshot]:
        """Get screenshots that don't have embeddings generated yet.

        Args:
            limit: Maximum number of screenshots to return

        Returns:
            List of screenshots without embeddings
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT * FROM screenshots
                WHERE (embedding_generated IS NULL OR embedding_generated = 0)
                AND analyzed = 1
                AND description IS NOT NULL
                AND description != ''
                ORDER BY timestamp DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            rows = cursor.fetchall()
            return [Screenshot(**dict(row)) for row in rows]

    def mark_embedding_generated(
        self,
        screenshot_id: int,
        model_name: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Mark screenshot as having embedding generated.

        Args:
            screenshot_id: Screenshot ID
            model_name: Name of embedding model used
            timestamp: Generation timestamp (defaults to now)

        Returns:
            True if successful
        """
        timestamp = timestamp or datetime.now()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE screenshots
                SET embedding_generated = 1,
                    embedding_model = ?,
                    embedding_generated_at = ?
                WHERE id = ?
                """,
                (model_name, timestamp, screenshot_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def mark_embeddings_generated_batch(
        self,
        screenshot_ids: List[int],
        model_name: str
    ) -> int:
        """Mark multiple screenshots as having embeddings generated.

        Args:
            screenshot_ids: List of screenshot IDs
            model_name: Name of embedding model used

        Returns:
            Number of screenshots updated
        """
        if not screenshot_ids:
            return 0

        timestamp = datetime.now()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(screenshot_ids))
            cursor.execute(
                f"""
                UPDATE screenshots
                SET embedding_generated = 1,
                    embedding_model = ?,
                    embedding_generated_at = ?
                WHERE id IN ({placeholders})
                """,
                [model_name, timestamp] + screenshot_ids
            )
            conn.commit()
            return cursor.rowcount

    def get_embedding_stats(self) -> Dict[str, int]:
        """Get statistics about embedding generation.

        Returns:
            Dictionary with embedding statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total screenshots
            cursor.execute("SELECT COUNT(*) FROM screenshots")
            total = cursor.fetchone()[0]

            # Analyzed screenshots
            cursor.execute("SELECT COUNT(*) FROM screenshots WHERE analyzed = 1")
            analyzed = cursor.fetchone()[0]

            # Screenshots with embeddings
            cursor.execute("SELECT COUNT(*) FROM screenshots WHERE embedding_generated = 1")
            with_embeddings = cursor.fetchone()[0]

            # Screenshots pending embedding
            cursor.execute("""
                SELECT COUNT(*) FROM screenshots
                WHERE analyzed = 1
                AND (embedding_generated IS NULL OR embedding_generated = 0)
            """)
            pending = cursor.fetchone()[0]

            return {
                "total_screenshots": total,
                "analyzed_screenshots": analyzed,
                "with_embeddings": with_embeddings,
                "pending_embeddings": pending
            }

    # Work session methods

    def create_work_session(self, start_time: datetime, end_time: Optional[datetime] = None) -> int:
        """Create a new work session.

        Args:
            start_time: Session start time
            end_time: Session end time (optional)

        Returns:
            Created session ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO work_sessions (start_time, end_time) VALUES (?, ?)",
                (start_time, end_time)
            )
            conn.commit()
            return cursor.lastrowid

    def update_work_session(self, session_id: int, **kwargs) -> bool:
        """Update work session fields.

        Args:
            session_id: Session ID
            **kwargs: Fields to update

        Returns:
            True if successful
        """
        if not kwargs:
            return False

        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [session_id]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE work_sessions SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_work_sessions(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
        """Get work sessions within date range.

        Args:
            start_date: Start date filter
            end_date: End date filter

        Returns:
            List of work sessions
        """
        query = "SELECT * FROM work_sessions WHERE 1=1"
        params = []

        if start_date:
            query += " AND start_time >= ?"
            params.append(start_date)
        if end_date:
            query += " AND start_time <= ?"
            params.append(end_date)

        query += " ORDER BY start_time DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # Activity summary methods

    def upsert_activity_summary(self, date: str, activity_type: str, total_seconds: int,
                                 screenshot_count: int, app_breakdown: str) -> bool:
        """Insert or update activity summary for a date.

        Args:
            date: Date string (YYYY-MM-DD)
            activity_type: Activity type
            total_seconds: Total seconds spent
            screenshot_count: Number of screenshots
            app_breakdown: JSON string of app usage

        Returns:
            True if successful
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO activity_summaries (date, activity_type, total_seconds, screenshot_count, app_breakdown)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(date, activity_type) DO UPDATE SET
                    total_seconds = excluded.total_seconds,
                    screenshot_count = excluded.screenshot_count,
                    app_breakdown = excluded.app_breakdown
                """,
                (date, activity_type, total_seconds, screenshot_count, app_breakdown)
            )
            conn.commit()
            return True

    def get_activity_summaries(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Get activity summaries within date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of activity summaries
        """
        query = "SELECT * FROM activity_summaries WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC, activity_type"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # Report methods

    def save_report(self, report_type: str, period_start: str, period_end: str, content: str, metadata: Optional[str] = None) -> int:
        """Save a generated report.

        Args:
            report_type: Type of report (daily, weekly, project)
            period_start: Start date
            period_end: End date
            content: Report content (Markdown)
            metadata: Optional JSON metadata

        Returns:
            Report ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO generated_reports (report_type, period_start, period_end, content, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (report_type, period_start, period_end, content, metadata)
            )
            conn.commit()
            return cursor.lastrowid

    def get_report(self, report_type: str, period_start: str) -> Optional[Dict]:
        """Get a specific report.

        Args:
            report_type: Report type
            period_start: Start date

        Returns:
            Report dictionary or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM generated_reports WHERE report_type = ? AND period_start = ? ORDER BY generated_at DESC LIMIT 1",
                (report_type, period_start)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_reports(self, report_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get recent reports.

        Args:
            report_type: Filter by report type (optional)
            limit: Maximum number of reports

        Returns:
            List of reports
        """
        query = "SELECT * FROM generated_reports WHERE 1=1"
        params = []

        if report_type:
            query += " AND report_type = ?"
            params.append(report_type)

        query += " ORDER BY period_start DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # TODO methods

    def create_todo(
        self,
        screenshot_id: Optional[int],
        todo_text: str,
        priority: str = "medium",
        title: Optional[str] = None,
        due_date: Optional[str] = None,
        created_by: str = "ai_extracted",
        notes: Optional[str] = None
    ) -> int:
        """Create a TODO item.

        Args:
            screenshot_id: Associated screenshot (optional)
            todo_text: TODO description
            priority: Priority level (low/medium/high)
            title: TODO title (optional)
            due_date: Due date in ISO format (optional)
            created_by: Creation method ('manual' or 'ai_extracted')
            notes: Additional notes (optional)

        Returns:
            TODO ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO extracted_todos
                (screenshot_id, todo_text, priority, title, due_date, created_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (screenshot_id, todo_text, priority, title, due_date, created_by, notes)
            )
            conn.commit()
            return cursor.lastrowid

    def get_todos(self, status: str = "pending", limit: int = 100) -> List[Dict]:
        """Get TODO items.

        Args:
            status: Filter by status (pending/completed/all)
            limit: Maximum number of results

        Returns:
            List of TODO items
        """
        query = "SELECT * FROM extracted_todos WHERE 1=1"
        params = []

        if status != "all":
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY extracted_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_todo_status(self, todo_id: int, status: str) -> bool:
        """Update TODO status.

        Args:
            todo_id: TODO ID
            status: New status (pending/completed)

        Returns:
            True if successful
        """
        completed_at = datetime.now() if status == "completed" else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE extracted_todos SET status = ?, completed_at = ? WHERE id = ?",
                (status, completed_at, todo_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_todo(self, todo_id: int) -> Optional[Dict]:
        """Get a single TODO item by ID.

        Args:
            todo_id: TODO ID

        Returns:
            TODO dict or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM extracted_todos WHERE id = ?", (todo_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_todo(
        self,
        todo_id: int,
        title: Optional[str] = None,
        todo_text: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update a TODO item.

        Args:
            todo_id: TODO ID
            title: New title (optional)
            todo_text: New description (optional)
            priority: New priority (optional)
            due_date: New due date (optional)
            notes: New notes (optional)

        Returns:
            True if successful
        """
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if todo_text is not None:
            updates.append("todo_text = ?")
            params.append(todo_text)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if not updates:
            return False

        params.append(todo_id)
        query = f"UPDATE extracted_todos SET {', '.join(updates)} WHERE id = ?"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_todo(self, todo_id: int) -> bool:
        """Delete a TODO item.

        Args:
            todo_id: TODO ID

        Returns:
            True if successful
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM extracted_todos WHERE id = ?", (todo_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_todos_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: str = "all",
        limit: int = 100
    ) -> List[Dict]:
        """Get TODOs within a date range.

        Args:
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            status: Filter by status (pending/completed/all)
            limit: Maximum number of results

        Returns:
            List of TODO items
        """
        query = "SELECT * FROM extracted_todos WHERE 1=1"
        params = []

        if start_date:
            query += " AND due_date >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND due_date <= ?"
            params.append(end_date.isoformat())
        if status != "all":
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY due_date ASC, priority DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


# Global database instance
db = Database()
