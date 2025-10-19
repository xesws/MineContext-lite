"""API routes for MineContext-v2."""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from backend.api.schemas import (
    AnalyzeResponse,
    CaptureNowResponse,
    CaptureStartRequest,
    CaptureStartResponse,
    CaptureStatusResponse,
    CaptureStopResponse,
    ContextSuggestionsRequest,
    ContextSuggestionsResponse,
    EmbeddingGenerationRequest,
    EmbeddingGenerationResponse,
    EmbeddingStatsResponse,
    ScreenshotDeleteResponse,
    ScreenshotResponse,
    ScreenshotSearchRequest,
    ScreenshotsListResponse,
    ScreenshotUpdateRequest,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SimilarScreenshotResponse,
    TimelineResponse,
)
from backend.capture import capture_service
from backend.config import settings
from backend.database import db
from backend.models import ScreenshotUpdate

router = APIRouter()


# Screenshot endpoints
@router.get("/screenshots", response_model=ScreenshotsListResponse)
async def list_screenshots(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
):
    """List all screenshots with pagination."""
    try:
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        screenshots = db.get_screenshots(
            limit=limit, offset=offset, start_date=start_dt, end_date=end_dt
        )
        total = db.get_total_screenshots()

        return ScreenshotsListResponse(
            screenshots=[ScreenshotResponse.model_validate(s) for s in screenshots],
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Error listing screenshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screenshots/{screenshot_id}", response_model=ScreenshotResponse)
async def get_screenshot(screenshot_id: int):
    """Get a specific screenshot by ID."""
    screenshot = db.get_screenshot(screenshot_id)
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    return ScreenshotResponse.model_validate(screenshot)


@router.patch("/screenshots/{screenshot_id}", response_model=ScreenshotResponse)
async def update_screenshot(screenshot_id: int, update: ScreenshotUpdateRequest):
    """Update screenshot metadata."""
    try:
        screenshot_update = ScreenshotUpdate(
            description=update.description, tags=update.tags
        )
        updated_screenshot = db.update_screenshot(screenshot_id, screenshot_update)

        if not updated_screenshot:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        return ScreenshotResponse.model_validate(updated_screenshot)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating screenshot {screenshot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/screenshots/{screenshot_id}", response_model=ScreenshotDeleteResponse)
async def delete_screenshot(screenshot_id: int):
    """Delete a screenshot."""
    try:
        # Get screenshot to find file path
        screenshot = db.get_screenshot(screenshot_id)
        if not screenshot:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        # Delete from database
        db.delete_screenshot(screenshot_id)

        # Delete file if it exists
        if os.path.exists(screenshot.filepath):
            os.remove(screenshot.filepath)
            logger.info(f"Deleted screenshot file: {screenshot.filepath}")

        return ScreenshotDeleteResponse(
            success=True, message=f"Screenshot {screenshot_id} deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting screenshot {screenshot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screenshots/search", response_model=ScreenshotsListResponse)
async def search_screenshots(search_request: ScreenshotSearchRequest):
    """Search screenshots by query, date range, or tags."""
    try:
        if search_request.query:
            # Text search in description/tags
            screenshots = db.search_screenshots(
                query=search_request.query,
                limit=search_request.limit,
                offset=search_request.offset,
            )
        else:
            # Date range filter
            screenshots = db.get_screenshots(
                limit=search_request.limit,
                offset=search_request.offset,
                start_date=search_request.start_date,
                end_date=search_request.end_date,
            )

        # Additional filtering by tags if provided
        if search_request.tags:
            tag_filter = search_request.tags.lower()
            screenshots = [
                s
                for s in screenshots
                if s.tags and tag_filter in s.tags.lower()
            ]

        return ScreenshotsListResponse(
            screenshots=[ScreenshotResponse.model_validate(s) for s in screenshots],
            total=len(screenshots),
            limit=search_request.limit,
            offset=search_request.offset,
        )
    except Exception as e:
        logger.error(f"Error searching screenshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline", response_model=List[TimelineResponse])
async def get_timeline(
    date: Optional[str] = Query(default=None, description="Date in YYYY-MM-DD format"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Get timeline view of screenshots grouped by date."""
    try:
        if date:
            # Get screenshots for specific date
            start_dt = datetime.fromisoformat(date)
            end_dt = datetime.fromisoformat(date).replace(
                hour=23, minute=59, second=59
            )
            screenshots = db.get_screenshots(
                limit=limit, start_date=start_dt, end_date=end_dt
            )

            return [
                TimelineResponse(
                    screenshots=[
                        ScreenshotResponse.model_validate(s) for s in screenshots
                    ],
                    date=date,
                    count=len(screenshots),
                )
            ]
        else:
            # Get recent screenshots grouped by date
            screenshots = db.get_screenshots(limit=limit)

            # Group by date
            timeline_dict = {}
            for screenshot in screenshots:
                date_str = screenshot.timestamp.strftime("%Y-%m-%d")
                if date_str not in timeline_dict:
                    timeline_dict[date_str] = []
                timeline_dict[date_str].append(screenshot)

            # Create timeline responses
            timeline = [
                TimelineResponse(
                    screenshots=[
                        ScreenshotResponse.model_validate(s) for s in screenshots_list
                    ],
                    date=date_str,
                    count=len(screenshots_list),
                )
                for date_str, screenshots_list in timeline_dict.items()
            ]

            return timeline
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Capture control endpoints
@router.post("/capture/start", response_model=CaptureStartResponse)
async def start_capture(request: CaptureStartRequest = None):
    """Start screenshot capture service."""
    try:
        if capture_service.is_running:
            return CaptureStartResponse(
                success=False,
                message="Capture service is already running",
                status=CaptureStatusResponse(**capture_service.get_status()),
            )

        # TODO: Support interval override if provided in request
        capture_service.start()
        logger.info("Screenshot capture started via API")

        return CaptureStartResponse(
            success=True,
            message="Screenshot capture started successfully",
            status=CaptureStatusResponse(**capture_service.get_status()),
        )
    except Exception as e:
        logger.error(f"Error starting capture: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture/stop", response_model=CaptureStopResponse)
async def stop_capture():
    """Stop screenshot capture service."""
    try:
        if not capture_service.is_running:
            return CaptureStopResponse(
                success=False,
                message="Capture service is not running",
                screenshots_captured=capture_service.screenshots_captured,
            )

        screenshots_captured = capture_service.screenshots_captured
        capture_service.stop()
        logger.info("Screenshot capture stopped via API")

        return CaptureStopResponse(
            success=True,
            message="Screenshot capture stopped successfully",
            screenshots_captured=screenshots_captured,
        )
    except Exception as e:
        logger.error(f"Error stopping capture: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capture/status", response_model=CaptureStatusResponse)
async def get_capture_status():
    """Get current capture service status."""
    try:
        return CaptureStatusResponse(**capture_service.get_status())
    except Exception as e:
        logger.error(f"Error getting capture status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture/now", response_model=CaptureNowResponse)
async def capture_now():
    """Capture a screenshot immediately (manual capture)."""
    try:
        screenshot_id = capture_service.capture_now()

        if screenshot_id:
            return CaptureNowResponse(
                success=True,
                screenshot_id=screenshot_id,
                message=f"Screenshot captured successfully (ID: {screenshot_id})",
            )
        else:
            return CaptureNowResponse(
                success=False,
                screenshot_id=None,
                message="Failed to capture screenshot",
            )
    except Exception as e:
        logger.error(f"Error capturing screenshot manually: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Analysis endpoints
@router.post("/screenshots/{screenshot_id}/analyze", response_model=AnalyzeResponse)
async def analyze_screenshot(screenshot_id: int, force_reanalysis: bool = False):
    """Analyze a screenshot with AI."""
    try:
        # Check if screenshot exists
        screenshot = db.get_screenshot(screenshot_id)
        if not screenshot:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        # Check if AI is enabled
        if not settings.ai.enabled:
            return AnalyzeResponse(
                success=False,
                screenshot_id=screenshot_id,
                description=None,
                tags=None,
                error="AI features are not enabled. Set ai.enabled=true in config.yaml",
            )

        # Skip if already analyzed and not forcing reanalysis
        if screenshot.analyzed and not force_reanalysis:
            return AnalyzeResponse(
                success=True,
                screenshot_id=screenshot_id,
                description=screenshot.description,
                tags=screenshot.tags,
                error=None,
            )

        # Import AI utilities
        from backend.utils.ai_utils import (
            analyze_screenshot_async,
            categorize_activity,
            extract_tags_from_description,
        )

        # Perform AI analysis
        success, result, error = await analyze_screenshot_async(screenshot.filepath)

        if not success:
            return AnalyzeResponse(
                success=False,
                screenshot_id=screenshot_id,
                description=None,
                tags=None,
                error=error or "AI analysis failed",
            )

        # Extract information from AI result
        description = result.get("description", "")
        activity_type = result.get("activity", "")
        ai_tags = result.get("tags", "")

        # Categorize activity
        activity_category = categorize_activity(description, activity_type)

        # Generate tags if not provided by AI
        if not ai_tags:
            tag_list = extract_tags_from_description(description)
            ai_tags = ", ".join(tag_list)

        # Add activity category to tags if not already present
        if activity_category not in ai_tags.lower():
            ai_tags = f"{activity_category}, {ai_tags}" if ai_tags else activity_category

        # Update screenshot in database
        screenshot_update = ScreenshotUpdate(
            description=description,
            tags=ai_tags,
            analyzed=True
        )
        updated_screenshot = db.update_screenshot(screenshot_id, screenshot_update)

        # Create activity record
        from backend.models import ActivityCreate
        activity = ActivityCreate(
            screenshot_id=screenshot_id,
            activity_type=activity_category,
            content=description
        )
        db.create_activity(activity)

        logger.info(f"Screenshot {screenshot_id} analyzed successfully")

        return AnalyzeResponse(
            success=True,
            screenshot_id=screenshot_id,
            description=description,
            tags=ai_tags,
            error=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing screenshot {screenshot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screenshots/analyze-batch")
async def analyze_screenshots_batch(limit: int = Query(default=10, ge=1, le=100)):
    """Analyze multiple unanalyzed screenshots in batch."""
    try:
        # Check if AI is enabled
        if not settings.ai.enabled:
            raise HTTPException(
                status_code=400,
                detail="AI features are not enabled. Set ai.enabled=true in config.yaml"
            )

        # Get unanalyzed screenshots
        all_screenshots = db.get_screenshots(limit=limit)
        unanalyzed = [s for s in all_screenshots if not s.analyzed]

        if not unanalyzed:
            return {
                "success": True,
                "message": "No unanalyzed screenshots found",
                "analyzed_count": 0,
                "failed_count": 0,
            }

        # Import AI utilities
        from backend.utils.ai_utils import (
            analyze_screenshot_async,
            categorize_activity,
            extract_tags_from_description,
        )

        analyzed_count = 0
        failed_count = 0

        for screenshot in unanalyzed:
            try:
                # Perform AI analysis
                success, result, error = await analyze_screenshot_async(screenshot.filepath)

                if success:
                    # Extract information
                    description = result.get("description", "")
                    activity_type = result.get("activity", "")
                    ai_tags = result.get("tags", "")

                    # Categorize activity
                    activity_category = categorize_activity(description, activity_type)

                    # Generate tags if needed
                    if not ai_tags:
                        tag_list = extract_tags_from_description(description)
                        ai_tags = ", ".join(tag_list)

                    if activity_category not in ai_tags.lower():
                        ai_tags = f"{activity_category}, {ai_tags}" if ai_tags else activity_category

                    # Update screenshot
                    screenshot_update = ScreenshotUpdate(
                        description=description,
                        tags=ai_tags,
                        analyzed=True
                    )
                    db.update_screenshot(screenshot.id, screenshot_update)

                    # Create activity record
                    from backend.models import ActivityCreate
                    activity = ActivityCreate(
                        screenshot_id=screenshot.id,
                        activity_type=activity_category,
                        content=description
                    )
                    db.create_activity(activity)

                    analyzed_count += 1
                    logger.info(f"Batch analysis: Screenshot {screenshot.id} analyzed")

                    # Auto-generate embedding if enabled
                    if settings.embeddings.enabled and settings.embeddings.auto_generate:
                        try:
                            from backend.utils.embedding_utils import embedding_service
                            from backend.vector_store import vector_store

                            if embedding_service.is_available() and vector_store.is_available():
                                embedding = embedding_service.generate_embedding(description)
                                if embedding is not None:
                                    vector_store.add_embedding(
                                        screenshot_id=screenshot.id,
                                        embedding=embedding,
                                        description=description,
                                        tags=ai_tags,
                                        timestamp=screenshot.timestamp
                                    )
                                    db.mark_embedding_generated(
                                        screenshot_id=screenshot.id,
                                        model_name=embedding_service.model_name
                                    )
                                    logger.debug(f"Auto-generated embedding for screenshot {screenshot.id}")
                        except Exception as embed_error:
                            logger.error(f"Error auto-generating embedding: {embed_error}")

                else:
                    failed_count += 1
                    logger.error(f"Batch analysis: Screenshot {screenshot.id} failed: {error}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Batch analysis: Error processing screenshot {screenshot.id}: {e}")

        return {
            "success": True,
            "message": f"Batch analysis completed",
            "analyzed_count": analyzed_count,
            "failed_count": failed_count,
            "total_processed": len(unanalyzed),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Semantic Search & Embedding endpoints
@router.post("/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """Search screenshots using semantic similarity."""
    try:
        from backend.vector_store import vector_store

        # Check if vector store is available
        if not vector_store.is_available():
            raise HTTPException(
                status_code=503,
                detail="Semantic search is not available. Vector database may not be initialized."
            )

        # Perform semantic search
        results = vector_store.search_by_text(
            query_text=request.query,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )

        # Convert to response format
        similar_screenshots = [
            SimilarScreenshotResponse(**result) for result in results
        ]

        return SemanticSearchResponse(
            query=request.query,
            results=similar_screenshots,
            count=len(similar_screenshots)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screenshots/{screenshot_id}/similar", response_model=List[SimilarScreenshotResponse])
async def find_similar_screenshots(
    screenshot_id: int,
    top_k: int = Query(default=10, ge=1, le=50, description="Number of similar screenshots to return")
):
    """Find screenshots similar to the given screenshot."""
    try:
        from backend.vector_store import vector_store

        # Check if screenshot exists
        screenshot = db.get_screenshot(screenshot_id)
        if not screenshot:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        # Check if vector store is available
        if not vector_store.is_available():
            raise HTTPException(
                status_code=503,
                detail="Semantic search is not available. Vector database may not be initialized."
            )

        # Get the screenshot's embedding
        vector_data = vector_store.get_by_id(screenshot_id)
        if not vector_data:
            raise HTTPException(
                status_code=404,
                detail="No embedding found for this screenshot. Generate embeddings first."
            )

        # Search for similar screenshots
        embedding = vector_data['embedding']
        similar_items = vector_store.search_similar(
            query_embedding=embedding,
            top_k=top_k + 1,  # +1 to exclude self
            min_similarity=settings.vector_db.similarity_threshold
        )

        # Filter out the screenshot itself
        similar_screenshots = [
            SimilarScreenshotResponse(**item)
            for item in similar_items
            if item['screenshot_id'] != screenshot_id
        ]

        return similar_screenshots[:top_k]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar screenshots for {screenshot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screenshots/{screenshot_id}/related", response_model=List[SimilarScreenshotResponse])
async def get_related_contexts(
    screenshot_id: int,
    max_results: int = Query(default=5, ge=1, le=20, description="Maximum number of related contexts")
):
    """Get contextually related screenshots using the context resurfacing service."""
    try:
        from backend.services.context_resurfacing import context_resurfacing_service

        # Check if screenshot exists
        screenshot = db.get_screenshot(screenshot_id)
        if not screenshot:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        # Check if service is available
        if not context_resurfacing_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Context resurfacing service is not available."
            )

        # Find related contexts
        related = context_resurfacing_service.find_related_contexts(
            screenshot_id=screenshot_id,
            max_results=max_results
        )

        # Convert to response format
        return [SimilarScreenshotResponse(**r.model_dump()) for r in related]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting related contexts for screenshot {screenshot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embeddings/generate-batch", response_model=EmbeddingGenerationResponse)
async def generate_embeddings_batch(request: EmbeddingGenerationRequest):
    """Generate embeddings for screenshots in batch."""
    try:
        from backend.utils.embedding_utils import embedding_service
        from backend.vector_store import vector_store

        # Check if services are available
        if not embedding_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Embedding service is not available. Check if the model is loaded."
            )

        if not vector_store.is_available():
            raise HTTPException(
                status_code=503,
                detail="Vector store is not available."
            )

        # Determine which screenshots to process
        if request.screenshot_ids:
            # Process specific screenshot IDs
            screenshots = [db.get_screenshot(sid) for sid in request.screenshot_ids]
            screenshots = [s for s in screenshots if s is not None]
        elif request.all_unprocessed:
            # Process all unprocessed screenshots
            screenshots = db.get_screenshots_without_embeddings(limit=None)
        else:
            raise HTTPException(
                status_code=400,
                detail="Must specify either screenshot_ids or all_unprocessed=true"
            )

        if not screenshots:
            return EmbeddingGenerationResponse(
                success=True,
                processed_count=0,
                failed_count=0,
                message="No screenshots to process"
            )

        # Filter out screenshots without descriptions
        valid_screenshots = [
            s for s in screenshots
            if s.description and s.description.strip()
        ]

        if not valid_screenshots:
            return EmbeddingGenerationResponse(
                success=False,
                processed_count=0,
                failed_count=len(screenshots),
                message="No screenshots with descriptions found"
            )

        # Generate embeddings
        texts = [s.description for s in valid_screenshots]
        batch_size = request.batch_size or settings.embeddings.batch_size

        embeddings, failed_indices = embedding_service.generate_embeddings_batch(
            texts=texts,
            batch_size=batch_size
        )

        # Store embeddings in vector store
        processed_count = 0
        failed_count = 0

        for i, screenshot in enumerate(valid_screenshots):
            if i in failed_indices:
                failed_count += 1
                continue

            try:
                # Add to vector store
                success = vector_store.add_embedding(
                    screenshot_id=screenshot.id,
                    embedding=embeddings[i],
                    description=screenshot.description,
                    tags=screenshot.tags,
                    timestamp=screenshot.timestamp
                )

                if success:
                    # Mark in database
                    db.mark_embedding_generated(
                        screenshot_id=screenshot.id,
                        model_name=embedding_service.model_name
                    )
                    processed_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error storing embedding for screenshot {screenshot.id}: {e}")
                failed_count += 1

        return EmbeddingGenerationResponse(
            success=True,
            processed_count=processed_count,
            failed_count=failed_count,
            message=f"Generated {processed_count} embeddings, {failed_count} failed"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating embeddings batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/embeddings/stats", response_model=EmbeddingStatsResponse)
async def get_embedding_stats():
    """Get statistics about embedding generation."""
    try:
        stats = db.get_embedding_stats()
        return EmbeddingStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context/suggestions", response_model=ContextSuggestionsResponse)
async def get_context_suggestions(request: ContextSuggestionsRequest):
    """Get proactive context suggestions based on current activity."""
    try:
        from backend.services.context_resurfacing import context_resurfacing_service

        # Check if service is available
        if not context_resurfacing_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Context resurfacing service is not available."
            )

        # Get suggestions
        suggestions = context_resurfacing_service.get_proactive_suggestions(
            current_context=request.current_context,
            max_suggestions=request.max_suggestions
        )

        # Convert to response format
        return ContextSuggestionsResponse(
            suggestions=[SimilarScreenshotResponse(**s.model_dump()) for s in suggestions],
            count=len(suggestions)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
