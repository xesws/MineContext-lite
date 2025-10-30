"""Pydantic models for TodoList module."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ===== UserTodo Models =====

class UserTodoBase(BaseModel):
    """Base model for user-defined TODO."""

    title: str = Field(..., description="TODO title", min_length=1, max_length=500)
    description: Optional[str] = Field(None, description="Detailed description of the TODO")
    parent_id: Optional[int] = Field(None, description="Parent TODO ID for subtasks")
    status: str = Field(default="pending", description="TODO status: pending/in_progress/completed/archived")
    priority: str = Field(default="medium", description="Priority level: low/medium/high")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    due_date: Optional[datetime] = Field(None, description="Due date for the TODO")
    estimated_hours: Optional[float] = Field(None, description="Estimated hours to complete")


class UserTodoCreate(UserTodoBase):
    """Model for creating a new TODO."""
    pass


class UserTodoUpdate(BaseModel):
    """Model for updating a TODO."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)


class UserTodo(UserTodoBase):
    """Full TODO model with database fields."""

    id: int = Field(..., description="TODO ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    completion_percentage: int = Field(default=0, description="Completion percentage (0-100)", ge=0, le=100)

    class Config:
        from_attributes = True


class UserTodoWithChildren(UserTodo):
    """TODO model with children (for tree structure)."""

    children: List['UserTodoWithChildren'] = Field(default=[], description="Child TODOs (subtasks)")


# Enable forward references
UserTodoWithChildren.model_rebuild()


# ===== TodoActivity Models =====

class TodoActivityBase(BaseModel):
    """Base model for TODO activity (screenshot link)."""

    todo_id: int = Field(..., description="Associated TODO ID")
    screenshot_id: int = Field(..., description="Associated screenshot ID")
    activity_description: Optional[str] = Field(None, description="Activity description")
    match_confidence: Optional[float] = Field(None, description="Matching confidence score (0-1)", ge=0, le=1)
    match_method: str = Field(default="semantic", description="Match method: semantic/keyword/manual")
    duration_minutes: Optional[int] = Field(None, description="Activity duration in minutes")
    activity_type: Optional[str] = Field(None, description="Activity type: reading/coding/video/browsing/general")


class TodoActivityCreate(TodoActivityBase):
    """Model for creating a new TODO activity link."""
    pass


class TodoActivity(TodoActivityBase):
    """Full TODO activity model with database fields."""

    id: int = Field(..., description="Activity ID")
    matched_at: datetime = Field(default_factory=datetime.now, description="Match timestamp")

    class Config:
        from_attributes = True


# ===== TodoProgressSnapshot Models =====

class TodoProgressSnapshotBase(BaseModel):
    """Base model for TODO progress snapshot."""

    todo_id: int = Field(..., description="Associated TODO ID")
    completed_aspects: str = Field(..., description="JSON array of completed aspects")
    remaining_aspects: str = Field(..., description="JSON array of remaining aspects")
    total_time_spent: int = Field(default=0, description="Total time spent in minutes")
    ai_summary: Optional[str] = Field(None, description="AI-generated progress summary")
    completion_percentage: int = Field(default=0, description="Completion percentage (0-100)", ge=0, le=100)
    next_steps: Optional[str] = Field(None, description="JSON array of recommended next steps")


class TodoProgressSnapshotCreate(TodoProgressSnapshotBase):
    """Model for creating a new progress snapshot."""
    pass


class TodoProgressSnapshot(TodoProgressSnapshotBase):
    """Full progress snapshot model with database fields."""

    id: int = Field(..., description="Snapshot ID")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

    class Config:
        from_attributes = True


# ===== Extended Models for API Responses =====

class TodoWithActivities(UserTodo):
    """TODO with associated activities."""

    activities: List[TodoActivity] = Field(default=[], description="Associated screenshot activities")
    total_time_spent: int = Field(default=0, description="Total time spent in minutes")


class TodoWithProgress(UserTodo):
    """TODO with latest progress snapshot."""

    latest_progress: Optional[TodoProgressSnapshot] = Field(None, description="Most recent progress snapshot")
    activities_count: int = Field(default=0, description="Number of associated activities")
    total_time_spent: int = Field(default=0, description="Total time spent in minutes")


class TodoDetailResponse(UserTodo):
    """Detailed TODO response with activities and progress."""

    children: List[UserTodo] = Field(default=[], description="Child TODOs (subtasks)")
    activities: List[TodoActivity] = Field(default=[], description="Associated screenshot activities")
    latest_progress: Optional[TodoProgressSnapshot] = Field(None, description="Most recent progress snapshot")
    total_time_spent: int = Field(default=0, description="Total time spent in minutes")
