"""API request/response schemas for MineContext-v2."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Request schemas
class CaptureStartRequest(BaseModel):
    """Request to start screenshot capture."""

    interval_seconds: Optional[int] = Field(None, description="Override default capture interval")


class CaptureNowRequest(BaseModel):
    """Request to capture a screenshot immediately."""

    pass


class ScreenshotAnalyzeRequest(BaseModel):
    """Request to analyze a screenshot with AI."""

    screenshot_id: int = Field(..., description="Screenshot ID to analyze")
    force_reanalysis: bool = Field(default=False, description="Force re-analysis even if already done")


class ScreenshotUpdateRequest(BaseModel):
    """Request to update screenshot metadata."""

    description: Optional[str] = Field(None, description="Screenshot description")
    tags: Optional[str] = Field(None, description="Comma-separated tags")


class ScreenshotSearchRequest(BaseModel):
    """Request to search screenshots."""

    query: Optional[str] = Field(None, description="Search query")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    tags: Optional[str] = Field(None, description="Tag filter")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


# Response schemas
class ScreenshotResponse(BaseModel):
    """Screenshot response."""

    id: int
    filepath: str
    timestamp: datetime
    image_hash: Optional[str]
    description: Optional[str]
    tags: Optional[str]
    app_name: Optional[str]
    window_title: Optional[str]
    analyzed: bool
    file_size: Optional[int]

    class Config:
        from_attributes = True


class ScreenshotsListResponse(BaseModel):
    """List of screenshots response."""

    screenshots: List[ScreenshotResponse]
    total: int
    limit: int
    offset: int


class CaptureStatusResponse(BaseModel):
    """Capture service status response."""

    is_running: bool
    interval_seconds: int
    screenshots_captured: int
    last_capture_time: Optional[datetime]


class CaptureStartResponse(BaseModel):
    """Response after starting capture."""

    success: bool
    message: str
    status: CaptureStatusResponse


class CaptureStopResponse(BaseModel):
    """Response after stopping capture."""

    success: bool
    message: str
    screenshots_captured: int


class CaptureNowResponse(BaseModel):
    """Response after manual screenshot capture."""

    success: bool
    screenshot_id: Optional[int]
    message: str


class ScreenshotDeleteResponse(BaseModel):
    """Response after deleting a screenshot."""

    success: bool
    message: str


class AnalyzeResponse(BaseModel):
    """Response after analyzing a screenshot."""

    success: bool
    screenshot_id: int
    description: Optional[str]
    tags: Optional[str]
    error: Optional[str]


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database_connected: bool
    capture_running: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class TimelineResponse(BaseModel):
    """Timeline view response."""

    screenshots: List[ScreenshotResponse]
    date: str
    count: int


# Semantic search schemas
class SemanticSearchRequest(BaseModel):
    """Request for semantic search."""

    query: str = Field(..., description="Search query text")
    top_k: Optional[int] = Field(default=10, description="Number of results to return")
    min_similarity: Optional[float] = Field(default=None, description="Minimum similarity threshold (0-1)")


class SimilarScreenshotResponse(BaseModel):
    """Similar screenshot result."""

    screenshot_id: int
    similarity: float
    description: Optional[str]
    tags: Optional[str]
    timestamp: Optional[str]


class SemanticSearchResponse(BaseModel):
    """Response for semantic search."""

    query: str
    results: List[SimilarScreenshotResponse]
    count: int


class EmbeddingGenerationRequest(BaseModel):
    """Request to generate embeddings."""

    screenshot_ids: Optional[List[int]] = Field(None, description="Specific screenshot IDs to process")
    all_unprocessed: bool = Field(default=False, description="Process all screenshots without embeddings")
    batch_size: Optional[int] = Field(default=None, description="Batch size for processing")


class EmbeddingGenerationResponse(BaseModel):
    """Response after generating embeddings."""

    success: bool
    processed_count: int
    failed_count: int
    message: str


class EmbeddingStatsResponse(BaseModel):
    """Response with embedding statistics."""

    total_screenshots: int
    analyzed_screenshots: int
    with_embeddings: int
    pending_embeddings: int


class ContextSuggestionsRequest(BaseModel):
    """Request for proactive context suggestions."""

    current_context: Optional[str] = Field(None, description="Current activity or context description")
    max_suggestions: Optional[int] = Field(default=5, description="Maximum number of suggestions")


class ContextSuggestionsResponse(BaseModel):
    """Response with context suggestions."""

    suggestions: List[SimilarScreenshotResponse]
    count: int
