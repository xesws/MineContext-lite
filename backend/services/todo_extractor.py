"""TODO extraction service for automatically finding tasks in screenshots."""

import re
from typing import Dict, List, Optional, Tuple

from loguru import logger

from backend.config import settings
from backend.database import db


# Enhanced TODO extraction prompt
TODO_EXTRACTION_PROMPT = """Analyze this screenshot and extract all TODO items, tasks, or action items you can find.

Look for:
1. Browser tabs with TODO markers or task-related keywords
2. Task lists in documents or notes
3. Action items in chat/email messages
4. Comments in code (TODO, FIXME, HACK, XXX)
5. Project management boards or kanban cards
6. Calendar events or reminders

For each TODO found, provide:
- **Task**: Clear description of the task
- **Priority**: High, Medium, or Low (based on urgency indicators)
- **Source**: Where you found it (e.g., "Code comment", "Browser tab", "Document")
- **Context**: Any relevant context or details

Format your response as:
TODO: [task description] | Priority: [High/Medium/Low] | Source: [location] | Context: [details]

If no TODOs found, respond with: NO_TODOS_FOUND
"""


class TodoExtractorService:
    """Service for extracting TODO items from screenshots."""

    def __init__(self):
        """Initialize TODO extractor service."""
        self.todo_patterns = [
            r'TODO:?\s*(.+)',
            r'FIXME:?\s*(.+)',
            r'HACK:?\s*(.+)',
            r'XXX:?\s*(.+)',
            r'\[ \]\s*(.+)',  # Markdown checkboxes
            r'- \[ \]\s*(.+)',  # GitHub-style checkboxes
        ]

    async def extract_todos_from_screenshot(
        self,
        screenshot_id: int,
        force_reanalysis: bool = False
    ) -> Dict:
        """Extract TODO items from a screenshot using AI.

        Args:
            screenshot_id: Screenshot ID
            force_reanalysis: Force re-extraction even if already done

        Returns:
            Dictionary with extraction results
        """
        try:
            # Get screenshot
            screenshot = db.get_screenshot(screenshot_id)
            if not screenshot:
                return {'success': False, 'error': 'Screenshot not found'}

            # Check if AI is enabled
            if not settings.ai.enabled:
                return {
                    'success': False,
                    'error': 'AI features not enabled',
                    'todos': []
                }

            # Use AI vision to extract TODOs
            from backend.utils.ai_utils import analyze_screenshot_async

            success, result, error = await analyze_screenshot_async(
                screenshot.filepath,
                prompt=TODO_EXTRACTION_PROMPT
            )

            if not success:
                return {
                    'success': False,
                    'error': error or 'AI extraction failed',
                    'todos': []
                }

            # Parse TODO items from AI response
            description = result.get('description', '')

            if 'NO_TODOS_FOUND' in description:
                return {
                    'success': True,
                    'todos': [],
                    'message': 'No TODOs found in screenshot'
                }

            todos = self._parse_todo_response(description)

            # Store in database
            stored_count = 0
            for todo in todos:
                try:
                    db.create_todo(
                        screenshot_id=screenshot_id,
                        todo_text=todo['task'],
                        priority=todo['priority'].lower()
                    )
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing TODO: {e}")

            return {
                'success': True,
                'todos': todos,
                'stored_count': stored_count
            }

        except Exception as e:
            logger.error(f"Error extracting TODOs from screenshot {screenshot_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'todos': []
            }

    def _parse_todo_response(self, response: str) -> List[Dict]:
        """Parse TODO items from AI response.

        Args:
            response: AI response text

        Returns:
            List of TODO dictionaries
        """
        todos = []

        # Split by lines and look for TODO pattern
        lines = response.split('\n')

        for line in lines:
            if 'TODO:' in line or 'Task:' in line:
                todo = self._parse_todo_line(line)
                if todo:
                    todos.append(todo)

        return todos

    def _parse_todo_line(self, line: str) -> Optional[Dict]:
        """Parse a single TODO line.

        Args:
            line: Line containing TODO information

        Returns:
            TODO dictionary or None
        """
        try:
            # Expected format: TODO: [task] | Priority: [priority] | Source: [source] | Context: [context]
            parts = line.split('|')

            task = ''
            priority = 'medium'
            source = 'unknown'
            context = ''

            for part in parts:
                part = part.strip()
                if 'TODO:' in part or 'Task:' in part:
                    task = part.split(':', 1)[1].strip()
                elif 'Priority:' in part:
                    priority = part.split(':', 1)[1].strip().lower()
                elif 'Source:' in part:
                    source = part.split(':', 1)[1].strip()
                elif 'Context:' in part:
                    context = part.split(':', 1)[1].strip()

            if task:
                return {
                    'task': task,
                    'priority': priority if priority in ['high', 'medium', 'low'] else 'medium',
                    'source': source,
                    'context': context
                }

            return None

        except Exception as e:
            logger.error(f"Error parsing TODO line: {e}")
            return None

    async def extract_todos_batch(
        self,
        limit: int = 10,
        days: int = 7
    ) -> Dict:
        """Extract TODOs from recent screenshots in batch.

        Args:
            limit: Maximum number of screenshots to process
            days: Only process screenshots from last N days

        Returns:
            Batch extraction results
        """
        try:
            from datetime import datetime, timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            screenshots = db.get_screenshots(
                start_date=cutoff_date,
                limit=limit * 2  # Get more to filter
            )

            # Filter only analyzed screenshots without TODOs extracted yet
            # (This is a simplification - in production, track TODO extraction separately)
            candidates = [s for s in screenshots if s.analyzed][:limit]

            total_todos = 0
            failed_count = 0

            for screenshot in candidates:
                result = await self.extract_todos_from_screenshot(screenshot.id)
                if result['success']:
                    total_todos += result.get('stored_count', 0)
                else:
                    failed_count += 1

            return {
                'success': True,
                'processed_screenshots': len(candidates),
                'total_todos_extracted': total_todos,
                'failed_count': failed_count
            }

        except Exception as e:
            logger.error(f"Error in batch TODO extraction: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_pending_todos(self, limit: int = 50) -> List[Dict]:
        """Get all pending TODO items.

        Args:
            limit: Maximum number of TODOs to return

        Returns:
            List of pending TODOs
        """
        try:
            return db.get_todos(status='pending', limit=limit)
        except Exception as e:
            logger.error(f"Error getting pending TODOs: {e}")
            return []

    def mark_todo_completed(self, todo_id: int) -> bool:
        """Mark a TODO as completed.

        Args:
            todo_id: TODO ID

        Returns:
            True if successful
        """
        try:
            return db.update_todo_status(todo_id, 'completed')
        except Exception as e:
            logger.error(f"Error marking TODO completed: {e}")
            return False


# Global TODO extractor service instance
todo_extractor = TodoExtractorService()
