"""TODO management API routes."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import db
from loguru import logger

router = APIRouter(prefix="/todos", tags=["TODOs"])


# Pydantic models
class TodoCreate(BaseModel):
    """Model for creating a TODO."""
    title: Optional[str] = None
    todo_text: str
    priority: str = "medium"
    due_date: Optional[str] = None
    screenshot_id: Optional[int] = None
    notes: Optional[str] = None


class TodoUpdate(BaseModel):
    """Model for updating a TODO."""
    title: Optional[str] = None
    todo_text: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None


class TodoResponse(BaseModel):
    """Model for TODO response."""
    id: int
    title: Optional[str] = None
    todo_text: str
    priority: str
    status: str
    due_date: Optional[str] = None
    screenshot_id: Optional[int] = None
    created_by: str
    extracted_at: str
    completed_at: Optional[str] = None
    notes: Optional[str] = None


@router.post("", response_model=TodoResponse, status_code=201)
async def create_todo(todo: TodoCreate):
    """Create a new TODO item manually.

    Args:
        todo: TODO creation data

    Returns:
        Created TODO item
    """
    try:
        # Validate priority
        if todo.priority not in ['low', 'medium', 'high']:
            raise HTTPException(status_code=400, detail="Priority must be 'low', 'medium', or 'high'")

        # Validate due_date format if provided
        if todo.due_date:
            try:
                datetime.fromisoformat(todo.due_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

        # Create TODO
        todo_id = db.create_todo(
            screenshot_id=todo.screenshot_id,
            todo_text=todo.todo_text,
            priority=todo.priority,
            title=todo.title,
            due_date=todo.due_date,
            created_by='manual',  # Mark as manually created
            notes=todo.notes
        )

        # Fetch and return created TODO
        created_todo = db.get_todo(todo_id)
        if not created_todo:
            raise HTTPException(status_code=500, detail="Failed to create TODO")

        return created_todo

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating TODO: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[TodoResponse])
async def get_todos(
    status: str = "pending",
    priority: Optional[str] = None,
    created_by: Optional[str] = None,
    limit: int = 100
):
    """Get TODO items with optional filters.

    Args:
        status: Filter by status (pending/completed/all)
        priority: Filter by priority (low/medium/high)
        created_by: Filter by creation method (manual/ai_extracted)
        limit: Maximum number of results

    Returns:
        List of TODO items
    """
    try:
        # Get all TODOs with status filter
        todos = db.get_todos(status=status, limit=limit)

        # Apply additional filters
        if priority:
            todos = [t for t in todos if t.get('priority') == priority]
        if created_by:
            todos = [t for t in todos if t.get('created_by') == created_by]

        return todos

    except Exception as e:
        logger.error(f"Error fetching TODOs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int):
    """Get a specific TODO item by ID.

    Args:
        todo_id: TODO ID

    Returns:
        TODO item details
    """
    try:
        todo = db.get_todo(todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="TODO not found")

        return todo

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo_update: TodoUpdate):
    """Update a TODO item.

    Args:
        todo_id: TODO ID
        todo_update: Fields to update

    Returns:
        Updated TODO item
    """
    try:
        # Check if TODO exists
        existing = db.get_todo(todo_id)
        if not existing:
            raise HTTPException(status_code=404, detail="TODO not found")

        # Validate priority if provided
        if todo_update.priority and todo_update.priority not in ['low', 'medium', 'high']:
            raise HTTPException(status_code=400, detail="Priority must be 'low', 'medium', or 'high'")

        # Validate due_date format if provided
        if todo_update.due_date:
            try:
                datetime.fromisoformat(todo_update.due_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due_date format. Use ISO format")

        # Update TODO
        success = db.update_todo(
            todo_id=todo_id,
            title=todo_update.title,
            todo_text=todo_update.todo_text,
            priority=todo_update.priority,
            due_date=todo_update.due_date,
            notes=todo_update.notes
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update TODO")

        # Return updated TODO
        updated = db.get_todo(todo_id)
        return updated

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(todo_id: int):
    """Delete a TODO item.

    Args:
        todo_id: TODO ID
    """
    try:
        # Check if TODO exists
        existing = db.get_todo(todo_id)
        if not existing:
            raise HTTPException(status_code=404, detail="TODO not found")

        # Delete TODO
        success = db.delete_todo(todo_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete TODO")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{todo_id}/complete", response_model=TodoResponse)
async def complete_todo(todo_id: int):
    """Mark a TODO as completed.

    Args:
        todo_id: TODO ID

    Returns:
        Updated TODO item
    """
    try:
        # Check if TODO exists
        existing = db.get_todo(todo_id)
        if not existing:
            raise HTTPException(status_code=404, detail="TODO not found")

        # Update status
        success = db.update_todo_status(todo_id, 'completed')
        if not success:
            raise HTTPException(status_code=500, detail="Failed to complete TODO")

        # Return updated TODO
        updated = db.get_todo(todo_id)
        return updated

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{todo_id}/reopen", response_model=TodoResponse)
async def reopen_todo(todo_id: int):
    """Reopen a completed TODO.

    Args:
        todo_id: TODO ID

    Returns:
        Updated TODO item
    """
    try:
        # Check if TODO exists
        existing = db.get_todo(todo_id)
        if not existing:
            raise HTTPException(status_code=404, detail="TODO not found")

        # Update status
        success = db.update_todo_status(todo_id, 'pending')
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reopen TODO")

        # Return updated TODO
        updated = db.get_todo(todo_id)
        return updated

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reopening TODO {todo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming/deadline", response_model=List[TodoResponse])
async def get_upcoming_todos(days: int = 3):
    """Get TODOs due within the next N days.

    Args:
        days: Number of days to look ahead (default: 3)

    Returns:
        List of upcoming TODO items
    """
    try:
        from datetime import timedelta

        now = datetime.now()
        end_date = now + timedelta(days=days)

        todos = db.get_todos_by_date_range(
            start_date=now,
            end_date=end_date,
            status='pending'
        )

        return todos

    except Exception as e:
        logger.error(f"Error fetching upcoming TODOs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
