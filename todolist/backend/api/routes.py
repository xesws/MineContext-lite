"""API routes for TodoList module."""

import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from loguru import logger

from todolist.backend.api.schemas import (
    ActivityDeleteResponse,
    ActivityLinkRequest,
    ActivityResponse,
    ActivityTimelineResponse,
    ApplySuggestionsRequest,
    DecomposeRequest,
    DecomposeResponse,
    ProgressResponse,
    SmartAnalyzeResponse,
    SubtaskPreview,
    TodoCreateRequest,
    TodoCreateResponse,
    TodoDeleteResponse,
    TodoDetailResponse,
    TodoListResponse,
    TodoResponse,
    TodoStatsResponse,
    TodoTreeResponse,
    TodoUpdateRequest,
    TodoUpdateResponse,
    TodoWithChildrenResponse,
)
from todolist.backend.services.todo_manager import get_todo_manager

router = APIRouter()


# ===== TODO Management Endpoints =====

@router.post("/todos", response_model=TodoCreateResponse, status_code=201)
async def create_todo(todo: TodoCreateRequest):
    """Create a new TODO with automatic embedding generation.

    Args:
        todo: TODO creation request

    Returns:
        Created TODO with metadata
    """
    try:
        manager = get_todo_manager()
        created_todo = manager.create_todo(
            title=todo.title,
            description=todo.description,
            parent_id=todo.parent_id,
            priority=todo.priority,
            tags=todo.tags,
            due_date=todo.due_date,
            estimated_hours=todo.estimated_hours
        )

        return TodoCreateResponse(
            **created_todo,
            message="TODO created successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating TODO: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/todos")
async def get_todos(
    status: Optional[str] = Query(None, description="Filter by status (pending/in_progress/completed/archived)"),
    parent_id: Optional[int] = Query(None, description="Filter by parent_id (-1 for root TODOs only)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    tree: bool = Query(False, description="Return tree structure instead of flat list")
):
    """Get list of TODOs with optional filters.

    Args:
        status: Filter by status
        parent_id: Filter by parent (-1 for root TODOs)
        limit: Maximum results
        offset: Pagination offset
        tree: Return hierarchical tree structure

    Returns:
        List of TODOs or tree structure
    """
    try:
        manager = get_todo_manager()

        if tree:
            # Return tree structure (without pagination fields)
            todos = manager.get_todo_tree()
            return {
                "todos": [TodoWithChildrenResponse(**todo) for todo in todos],
                "total": len(todos),
                "tree_view": True
            }
        else:
            # Return flat list
            todos = manager.get_todos(
                status=status,
                parent_id=parent_id,
                limit=limit,
                offset=offset
            )
            total = manager.get_stats()['total_todos']

            return TodoListResponse(
                todos=[TodoResponse(**todo) for todo in todos],
                total=total,
                limit=limit,
                offset=offset
            )

    except Exception as e:
        logger.error(f"Error getting TODOs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/todos/{todo_id}", response_model=TodoDetailResponse)
async def get_todo(todo_id: int):
    """Get a single TODO with full details (activities, progress, children).

    Args:
        todo_id: TODO ID

    Returns:
        Detailed TODO information
    """
    try:
        manager = get_todo_manager()
        todo = manager.get_todo_with_details(todo_id)

        if not todo:
            raise HTTPException(status_code=404, detail=f"TODO with ID {todo_id} not found")

        # Parse JSON fields in latest_progress if present
        if todo.get('latest_progress'):
            progress = todo['latest_progress']
            progress['completed_aspects'] = json.loads(progress.get('completed_aspects', '[]'))
            progress['remaining_aspects'] = json.loads(progress.get('remaining_aspects', '[]'))
            progress['next_steps'] = json.loads(progress.get('next_steps', '[]'))

        return TodoDetailResponse(**todo)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/todos/{todo_id}", response_model=TodoUpdateResponse)
async def update_todo(todo_id: int, update: TodoUpdateRequest):
    """Update a TODO.

    If title or description is updated, embedding is automatically regenerated.

    Args:
        todo_id: TODO ID
        update: Fields to update

    Returns:
        Updated TODO
    """
    try:
        manager = get_todo_manager()

        # Filter out None values
        update_data = update.model_dump(exclude_unset=True)

        if not update_data:
            # Nothing to update
            todo = manager.get_todo(todo_id)
            if not todo:
                raise HTTPException(status_code=404, detail=f"TODO with ID {todo_id} not found")
            return TodoUpdateResponse(**todo, message="No changes to update")

        updated_todo = manager.update_todo(todo_id, **update_data)

        if not updated_todo:
            raise HTTPException(status_code=404, detail=f"TODO with ID {todo_id} not found")

        return TodoUpdateResponse(
            **updated_todo,
            message="TODO updated successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/todos/{todo_id}", response_model=TodoDeleteResponse)
async def delete_todo(todo_id: int):
    """Delete a TODO (cascading delete of children and activities).

    Args:
        todo_id: TODO ID

    Returns:
        Deletion confirmation
    """
    try:
        manager = get_todo_manager()
        success = manager.delete_todo(todo_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"TODO with ID {todo_id} not found")

        return TodoDeleteResponse(
            success=True,
            message=f"TODO {todo_id} deleted successfully",
            deleted_todo_id=todo_id
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Activity Management Endpoints =====

@router.get("/todos/{todo_id}/activities", response_model=ActivityTimelineResponse)
async def get_todo_activities(
    todo_id: int,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum results")
):
    """Get activity timeline for a TODO.

    Args:
        todo_id: TODO ID
        limit: Maximum results

    Returns:
        Activity timeline with total time spent
    """
    try:
        manager = get_todo_manager()

        # Check if TODO exists
        todo = manager.get_todo(todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail=f"TODO with ID {todo_id} not found")

        # Get activities
        activities = manager.get_todo_activities(todo_id, limit=limit)

        # Calculate total time from database
        from todolist.backend import database as todo_db
        total_time = todo_db.calculate_total_time_spent(manager.conn, todo_id)

        return ActivityTimelineResponse(
            todo_id=todo_id,
            activities=[ActivityResponse(**activity) for activity in activities],
            total_activities=len(activities),
            total_time_spent=total_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activities for TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activities/link", status_code=201)
async def link_activity(link: ActivityLinkRequest):
    """Manually link a screenshot to a TODO.

    Args:
        link: Activity link request

    Returns:
        Created activity information
    """
    try:
        manager = get_todo_manager()

        activity_id = manager.link_activity(
            todo_id=link.todo_id,
            screenshot_id=link.screenshot_id,
            activity_description=link.activity_description,
            duration_minutes=link.duration_minutes,
            match_method="manual"
        )

        return {
            "success": True,
            "activity_id": activity_id,
            "message": f"Screenshot {link.screenshot_id} linked to TODO {link.todo_id}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error linking activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/activities/{activity_id}", response_model=ActivityDeleteResponse)
async def unlink_activity(activity_id: int):
    """Delete an activity link.

    Args:
        activity_id: Activity ID

    Returns:
        Deletion confirmation
    """
    try:
        manager = get_todo_manager()
        success = manager.unlink_activity(activity_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Activity with ID {activity_id} not found")

        return ActivityDeleteResponse(
            success=True,
            message=f"Activity {activity_id} deleted successfully",
            deleted_activity_id=activity_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting activity {activity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screenshots/{screenshot_id}/todos")
async def get_screenshot_todos(screenshot_id: int):
    """Get all TODOs associated with a screenshot.

    Args:
        screenshot_id: Screenshot ID

    Returns:
        List of associated TODOs
    """
    try:
        from todolist.backend import database as todo_db
        manager = get_todo_manager()

        activities = todo_db.get_activities_by_screenshot(manager.conn, screenshot_id)

        # Extract unique TODOs
        todo_ids = list(set([activity['todo_id'] for activity in activities]))

        todos = []
        for todo_id in todo_ids:
            todo = manager.get_todo(todo_id)
            if todo:
                todos.append(TodoResponse(**todo))

        return {
            "screenshot_id": screenshot_id,
            "todos": todos,
            "count": len(todos)
        }

    except Exception as e:
        logger.error(f"Error getting TODOs for screenshot {screenshot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Progress Analysis Endpoints (Stubs for Phase 3) =====

@router.get("/todos/{todo_id}/progress", response_model=ProgressResponse)
async def get_todo_progress(
    todo_id: int,
    force_reanalysis: bool = Query(False, description="Force AI reanalysis")
):
    """Get TODO progress analysis (currently returns cached data, full AI analysis in Phase 3).

    Args:
        todo_id: TODO ID
        force_reanalysis: Force AI reanalysis

    Returns:
        Progress analysis
    """
    try:
        from todolist.backend import database as todo_db
        manager = get_todo_manager()

        # Check if TODO exists
        todo = manager.get_todo(todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail=f"TODO with ID {todo_id} not found")

        # Get latest progress snapshot
        latest_progress = todo_db.get_latest_progress_snapshot(manager.conn, todo_id)

        if not latest_progress:
            # No progress snapshot yet - return basic info
            return ProgressResponse(
                todo_id=todo_id,
                completed_aspects=[],
                remaining_aspects=[],
                completion_percentage=todo.get('completion_percentage', 0),
                summary="No progress analysis available yet. Activity matching and AI analysis coming in Phase 3.",
                next_steps=[],
                total_time_spent=0,
                analyzed_at=todo['updated_at']
            )

        # Parse JSON fields
        return ProgressResponse(
            todo_id=todo_id,
            completed_aspects=json.loads(latest_progress['completed_aspects']),
            remaining_aspects=json.loads(latest_progress['remaining_aspects']),
            completion_percentage=latest_progress['completion_percentage'],
            summary=latest_progress['ai_summary'],
            next_steps=json.loads(latest_progress['next_steps']),
            total_time_spent=latest_progress['total_time_spent'],
            analyzed_at=latest_progress['analyzed_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress for TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/todos/{todo_id}/analyze", response_model=ProgressResponse)
async def trigger_analysis(todo_id: int, force_reanalysis: bool = Query(False, description="Force reanalysis")):
    """Trigger AI progress analysis for a TODO.

    Args:
        todo_id: TODO ID
        force_reanalysis: Force new analysis even if cache exists

    Returns:
        Progress analysis response
    """
    try:
        from todolist.backend.services.progress_analyzer import ProgressAnalyzer
        manager = get_todo_manager()

        # Check if TODO exists
        todo = manager.get_todo(todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail=f"TODO with ID {todo_id} not found")

        # Create analyzer and run analysis
        analyzer = ProgressAnalyzer(manager.conn)
        analysis = await analyzer.analyze_todo_progress(todo_id, force_reanalysis=force_reanalysis)

        # Check for errors
        if 'error' in analysis:
            raise HTTPException(status_code=500, detail=analysis['error'])

        return ProgressResponse(**analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering analysis for TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Statistics Endpoint =====

@router.get("/stats", response_model=TodoStatsResponse)
async def get_todo_stats():
    """Get TODO statistics.

    Returns:
        Overall TODO statistics
    """
    try:
        manager = get_todo_manager()
        stats = manager.get_stats()

        return TodoStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting TODO stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Import/Export Endpoints =====

@router.post("/import/markdown")
async def import_from_markdown(content: str = Body(..., embed=True)):
    """Import TODOs from Markdown text.

    Args:
        content: Markdown formatted text

    Returns:
        Import results
    """
    try:
        from todolist.backend.services.import_export import ImportExportService
        manager = get_todo_manager()

        service = ImportExportService(manager.conn)
        result = service.import_from_markdown(content)

        return result

    except Exception as e:
        logger.error(f"Error importing from Markdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/json")
async def import_from_json(data: dict = Body(...)):
    """Import TODOs from JSON data.

    Args:
        data: JSON dictionary with TODOs

    Returns:
        Import results
    """
    try:
        from todolist.backend.services.import_export import ImportExportService
        manager = get_todo_manager()

        service = ImportExportService(manager.conn)
        result = service.import_from_json(data)

        return result

    except Exception as e:
        logger.error(f"Error importing from JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/markdown")
async def export_to_markdown(status: Optional[str] = None):
    """Export TODOs to Markdown format.

    Args:
        status: Optional status filter

    Returns:
        Markdown formatted text
    """
    try:
        from todolist.backend.services.import_export import ImportExportService
        from fastapi.responses import PlainTextResponse
        manager = get_todo_manager()

        service = ImportExportService(manager.conn)
        markdown = service.export_to_markdown(status_filter=status)

        return PlainTextResponse(
            content=markdown,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            }
        )

    except Exception as e:
        logger.error(f"Error exporting to Markdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/json")
async def export_to_json(status: Optional[str] = None):
    """Export TODOs to JSON format.

    Args:
        status: Optional status filter

    Returns:
        JSON formatted text
    """
    try:
        from todolist.backend.services.import_export import ImportExportService
        from fastapi.responses import PlainTextResponse
        manager = get_todo_manager()

        service = ImportExportService(manager.conn)
        json_data = service.export_to_json(status_filter=status)

        return PlainTextResponse(
            content=json_data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )

    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Smart TODO Analysis Endpoints =====

@router.post("/todos/{todo_id}/smart-analyze", response_model=SmartAnalyzeResponse)
async def smart_analyze_todo(todo_id: int):
    """Intelligently analyze TODO and generate update suggestions.

    Analyzes TODO activities and subtasks to generate suggestions for:
    - Progress updates (auto-applied)
    - Marking as complete (requires confirmation)
    - Creating new subtasks (requires confirmation)

    Args:
        todo_id: TODO ID to analyze

    Returns:
        Analysis results with auto-applied updates and suggestions for confirmation
    """
    try:
        from todolist.backend.services.todo_updater import TodoAutoUpdater
        manager = get_todo_manager()

        # Check if TODO exists
        todo = manager.get_todo(todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail=f"TODO with ID {todo_id} not found")

        # Create updater and analyze
        updater = TodoAutoUpdater(manager.conn)
        result = await updater.analyze_and_generate_suggestions(todo_id)

        # Auto-apply simple suggestions
        auto_suggestions = result.get('auto_suggestions', [])
        if auto_suggestions:
            await updater.apply_suggestions(todo_id, auto_suggestions)

        # Return response
        return SmartAnalyzeResponse(
            auto_applied=auto_suggestions,
            suggestions=result.get('confirm_suggestions', []),
            current_progress=result.get('progress', 0),
            analyzed_at=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in smart analyze for TODO {todo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/todos/{todo_id}/apply-suggestions", response_model=TodoUpdateResponse)
async def apply_todo_suggestions(
    todo_id: int,
    request: ApplySuggestionsRequest
):
    """Apply user-approved suggestions to a TODO.

    Args:
        todo_id: TODO ID
        request: List of approved suggestions

    Returns:
        Updated TODO
    """
    try:
        from todolist.backend.services.todo_updater import TodoAutoUpdater
        manager = get_todo_manager()

        # Check if TODO exists
        todo = manager.get_todo(todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail=f"TODO with ID {todo_id} not found")

        # Create updater and apply suggestions
        updater = TodoAutoUpdater(manager.conn)

        # Convert pydantic models to dicts
        suggestions_list = [s.dict() for s in request.suggestions]

        await updater.apply_suggestions(todo_id, suggestions_list)

        # Get updated TODO
        updated_todo = manager.get_todo(todo_id)

        return TodoUpdateResponse(
            **updated_todo,
            message="Suggestions applied successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying suggestions to TODO {todo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/todos/{todo_id}/decompose", response_model=DecomposeResponse)
async def decompose_existing_todo(todo_id: int):
    """AI decompose an existing TODO into subtasks.

    Args:
        todo_id: TODO ID to decompose

    Returns:
        Suggested subtasks
    """
    try:
        from todolist.backend.services.task_decomposer import TaskDecomposer
        manager = get_todo_manager()

        # Check if TODO exists
        todo = manager.get_todo(todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail=f"TODO with ID {todo_id} not found")

        # Create decomposer and decompose task
        decomposer = TaskDecomposer()
        subtasks = await decomposer.decompose_task(
            title=todo['title'],
            description=todo.get('description'),
            estimated_hours=todo.get('estimated_hours')
        )

        # Convert to response format
        subtask_previews = [SubtaskPreview(**st) for st in subtasks]

        return DecomposeResponse(suggested_subtasks=subtask_previews)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error decomposing TODO {todo_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/todos/preview-decompose", response_model=DecomposeResponse)
async def preview_task_decomposition(request: DecomposeRequest):
    """Preview task decomposition before creating TODO.

    Used during TODO creation to show AI-suggested subtasks.

    Args:
        request: Task information for decomposition

    Returns:
        Suggested subtasks
    """
    try:
        from todolist.backend.services.task_decomposer import TaskDecomposer

        # Validate title
        if not request.title or len(request.title.strip()) == 0:
            raise HTTPException(status_code=400, detail="Title is required")

        # Create decomposer and decompose task
        decomposer = TaskDecomposer()
        subtasks = await decomposer.decompose_task(
            title=request.title,
            description=request.description,
            estimated_hours=request.estimated_hours
        )

        # Convert to response format
        subtask_previews = [SubtaskPreview(**st) for st in subtasks]

        return DecomposeResponse(suggested_subtasks=subtask_previews)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in preview decompose: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
