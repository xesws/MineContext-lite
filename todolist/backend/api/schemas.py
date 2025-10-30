"""API request/response schemas for TodoList module."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ===== TODO Request Schemas =====

class TodoCreateRequest(BaseModel):
    """Request to create a new TODO."""

    title: str = Field(..., description="TODO title", min_length=1, max_length=500)
    description: Optional[str] = Field(None, description="Detailed description")
    parent_id: Optional[int] = Field(None, description="Parent TODO ID for subtasks")
    priority: str = Field(default="medium", description="Priority: low/medium/high")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_hours: Optional[float] = Field(None, description="Estimated hours to complete")


class TodoUpdateRequest(BaseModel):
    """Request to update a TODO."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = Field(None, description="Status: pending/in_progress/completed/archived")
    priority: Optional[str] = Field(None, description="Priority: low/medium/high")
    tags: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)


# ===== TODO Response Schemas =====

class TodoResponse(BaseModel):
    """Basic TODO response."""

    id: int
    title: str
    description: Optional[str]
    parent_id: Optional[int]
    status: str
    priority: str
    tags: Optional[str]
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    estimated_hours: Optional[float]
    completion_percentage: int

    class Config:
        from_attributes = True


class TodoWithChildrenResponse(TodoResponse):
    """TODO response with children (tree structure)."""

    children: List['TodoWithChildrenResponse'] = Field(default=[], description="Child TODOs")


# Enable forward references
TodoWithChildrenResponse.model_rebuild()


class TodoTreeResponse(BaseModel):
    """Response for tree-structured TODO list."""

    todos: List[TodoWithChildrenResponse]
    total: int


class TodoListResponse(BaseModel):
    """Response for flat TODO list."""

    todos: List[TodoResponse]
    total: int
    limit: int
    offset: int


# ===== Activity Request/Response Schemas =====

class ActivityLinkRequest(BaseModel):
    """Request to manually link a screenshot to a TODO."""

    todo_id: int = Field(..., description="TODO ID")
    screenshot_id: int = Field(..., description="Screenshot ID")
    activity_description: Optional[str] = Field(None, description="Activity description")
    duration_minutes: Optional[int] = Field(None, description="Activity duration in minutes")


class ActivityResponse(BaseModel):
    """Activity (screenshot-TODO link) response."""

    id: int
    todo_id: int
    screenshot_id: int
    activity_description: Optional[str]
    matched_at: datetime
    match_confidence: Optional[float]
    match_method: str
    duration_minutes: Optional[int]
    activity_type: Optional[str]
    # Additional fields from JOIN
    screenshot_timestamp: Optional[datetime] = None
    screenshot_description: Optional[str] = None
    screenshot_filepath: Optional[str] = None

    class Config:
        from_attributes = True


class ActivityTimelineResponse(BaseModel):
    """Response for TODO activity timeline."""

    todo_id: int
    activities: List[ActivityResponse]
    total_activities: int
    total_time_spent: int  # in minutes


# ===== Progress Response Schemas =====

class ProgressResponse(BaseModel):
    """Response for TODO progress analysis."""

    todo_id: int
    completed_aspects: List[str] = Field(default=[], description="Completed items")
    remaining_aspects: List[str] = Field(default=[], description="Remaining items")
    completion_percentage: int = Field(..., ge=0, le=100)
    summary: str = Field(default="", description="AI-generated summary")
    next_steps: List[str] = Field(default=[], description="Recommended next steps")
    total_time_spent: int = Field(default=0, description="Total time in minutes")
    analyzed_at: datetime


class TodoDetailResponse(TodoResponse):
    """Detailed TODO response with activities and progress."""

    children: List[TodoResponse] = Field(default=[], description="Child TODOs")
    activities: List[ActivityResponse] = Field(default=[], description="Associated activities")
    latest_progress: Optional[ProgressResponse] = Field(None, description="Latest progress snapshot")
    total_time_spent: int = Field(default=0, description="Total time in minutes")
    activities_count: int = Field(default=0, description="Number of activities")


# ===== Statistics Response =====

class TodoStatsResponse(BaseModel):
    """TODO statistics response."""

    total_todos: int
    pending: int
    in_progress: int
    completed: int
    overdue: int
    total_activities: int


# ===== Generic Response Schemas =====

class TodoDeleteResponse(BaseModel):
    """Response for TODO deletion."""

    success: bool
    message: str
    deleted_todo_id: int


class ActivityDeleteResponse(BaseModel):
    """Response for activity deletion."""

    success: bool
    message: str
    deleted_activity_id: int


class TodoCreateResponse(TodoResponse):
    """Response after creating a TODO."""

    message: str = Field(default="TODO created successfully")


class TodoUpdateResponse(TodoResponse):
    """Response after updating a TODO."""

    message: str = Field(default="TODO updated successfully")


# ===== Smart Analyze Schemas =====

class SuggestionItem(BaseModel):
    """Individual suggestion from smart analysis."""

    type: str = Field(..., description="Suggestion type: mark_complete, create_subtask, update_progress, update_status")
    data: Optional[dict] = Field(None, description="Suggestion data (varies by type)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score")
    reason: str = Field(..., description="Reason for this suggestion")


class SmartAnalyzeResponse(BaseModel):
    """Response from smart TODO analysis."""

    auto_applied: List[SuggestionItem] = Field(default=[], description="Auto-applied updates")
    suggestions: List[SuggestionItem] = Field(default=[], description="Suggestions requiring user confirmation")
    current_progress: int = Field(..., ge=0, le=100, description="Current progress percentage")
    analyzed_at: datetime = Field(..., description="Analysis timestamp")


class ApplySuggestionsRequest(BaseModel):
    """Request to apply selected suggestions."""

    suggestions: List[SuggestionItem] = Field(..., description="Approved suggestions to apply")


class DecomposeRequest(BaseModel):
    """Request for task decomposition preview."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    estimated_hours: Optional[float] = None


class SubtaskPreview(BaseModel):
    """Preview of a suggested subtask."""

    title: str
    description: Optional[str] = None
    estimated_hours: Optional[float] = None
    priority: str = Field(default="medium")


class DecomposeResponse(BaseModel):
    """Response from task decomposition."""

    suggested_subtasks: List[SubtaskPreview] = Field(..., description="AI-generated subtask suggestions")
