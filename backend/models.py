"""Pydantic models for MineContext-v2."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ScreenshotBase(BaseModel):
    """Base screenshot model."""

    filepath: str = Field(..., description="Path to screenshot file")
    image_hash: Optional[str] = Field(None, description="Perceptual hash of the image")
    description: Optional[str] = Field(None, description="AI-generated description")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    app_name: Optional[str] = Field(None, description="Active application name")
    window_title: Optional[str] = Field(None, description="Window title")
    file_size: Optional[int] = Field(None, description="File size in bytes")


class ScreenshotCreate(ScreenshotBase):
    """Model for creating a new screenshot."""

    pass


class Screenshot(ScreenshotBase):
    """Full screenshot model with database fields."""

    id: int = Field(..., description="Screenshot ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Capture timestamp")
    analyzed: bool = Field(default=False, description="Whether AI analysis has been performed")

    class Config:
        from_attributes = True


class ScreenshotUpdate(BaseModel):
    """Model for updating a screenshot."""

    description: Optional[str] = None
    tags: Optional[str] = None
    analyzed: Optional[bool] = None


class ActivityBase(BaseModel):
    """Base activity model."""

    screenshot_id: int = Field(..., description="Associated screenshot ID")
    activity_type: str = Field(..., description="Type of activity (coding, browsing, etc.)")
    content: Optional[str] = Field(None, description="Activity content/description")


class ActivityCreate(ActivityBase):
    """Model for creating a new activity."""

    pass


class Activity(ActivityBase):
    """Full activity model with database fields."""

    id: int = Field(..., description="Activity ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Activity timestamp")

    class Config:
        from_attributes = True


class CaptureStatus(BaseModel):
    """Capture service status."""

    is_running: bool = Field(..., description="Whether capture is active")
    interval_seconds: int = Field(..., description="Capture interval")
    screenshots_captured: int = Field(default=0, description="Total screenshots captured")
    last_capture_time: Optional[datetime] = Field(None, description="Last capture timestamp")


class AnalysisRequest(BaseModel):
    """Request model for screenshot analysis."""

    screenshot_id: int = Field(..., description="Screenshot ID to analyze")
    force_reanalysis: bool = Field(default=False, description="Force re-analysis even if already done")


class AnalysisResponse(BaseModel):
    """Response model for screenshot analysis."""

    screenshot_id: int = Field(..., description="Screenshot ID")
    description: str = Field(..., description="Generated description")
    tags: Optional[str] = Field(None, description="Generated tags")
    success: bool = Field(..., description="Whether analysis succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")


class SearchQuery(BaseModel):
    """Search query model."""

    query: Optional[str] = Field(None, description="Text search query")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    tags: Optional[str] = Field(None, description="Tag filter")
    limit: int = Field(default=100, description="Maximum results to return")
    offset: int = Field(default=0, description="Result offset for pagination")


class HealthCheck(BaseModel):
    """Health check response."""

    status: str = Field(default="ok", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    database_connected: bool = Field(..., description="Database connection status")
    capture_running: bool = Field(..., description="Capture service status")


class SimilarScreenshot(BaseModel):
    """Model for similar screenshot result."""

    screenshot_id: int = Field(..., description="Screenshot ID")
    similarity: float = Field(..., description="Similarity score (0-1)")
    description: Optional[str] = Field(None, description="Screenshot description")
    tags: Optional[str] = Field(None, description="Screenshot tags")
    timestamp: Optional[str] = Field(None, description="Screenshot timestamp")


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., description="Search query text")
    top_k: Optional[int] = Field(default=10, description="Number of results to return")
    min_similarity: Optional[float] = Field(default=None, description="Minimum similarity threshold (0-1)")


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""

    query: str = Field(..., description="Original query")
    results: List[SimilarScreenshot] = Field(default=[], description="Search results")
    count: int = Field(..., description="Number of results returned")


class EmbeddingGenerationRequest(BaseModel):
    """Request model for generating embeddings."""

    screenshot_ids: Optional[List[int]] = Field(None, description="Specific screenshot IDs to process")
    all_unprocessed: bool = Field(default=False, description="Process all screenshots without embeddings")
    batch_size: Optional[int] = Field(default=None, description="Batch size for processing")


class EmbeddingGenerationResponse(BaseModel):
    """Response model for embedding generation."""

    success: bool = Field(..., description="Whether operation succeeded")
    processed_count: int = Field(default=0, description="Number of embeddings generated")
    failed_count: int = Field(default=0, description="Number of failures")
    message: str = Field(..., description="Status message")
