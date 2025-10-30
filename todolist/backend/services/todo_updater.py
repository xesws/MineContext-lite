"""TodoAutoUpdater service - Intelligent TODO auto-update engine."""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from todolist.backend import database as todo_db
from todolist.backend.services.activity_matcher import ActivityMatcher
from todolist.backend.services.progress_analyzer import ProgressAnalyzer
from todolist.backend.services.todo_manager import TodoManager


class TodoAutoUpdater:
    """Service for intelligently analyzing and auto-updating TODOs."""

    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize TodoAutoUpdater.

        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.activity_matcher = ActivityMatcher(db_connection)
        self.progress_analyzer = ProgressAnalyzer(db_connection)
        self.todo_manager = TodoManager(db_connection)

    async def analyze_and_generate_suggestions(self, todo_id: int) -> Dict:
        """Analyze TODO and generate update suggestions.

        Args:
            todo_id: TODO ID to analyze

        Returns:
            Dictionary with:
            {
                'auto_suggestions': [  # Auto-applied updates
                    {
                        'type': 'update_progress',
                        'data': {'percentage': 60},
                        'reason': '3/5 subtasks completed'
                    }
                ],
                'confirm_suggestions': [  # User confirmation required
                    {
                        'type': 'mark_complete',
                        'confidence': 0.95,
                        'reason': 'All subtasks completed'
                    },
                    {
                        'type': 'create_subtask',
                        'data': {
                            'title': 'Implement login',
                            'description': '...'
                        },
                        'confidence': 0.85,
                        'reason': 'Detected related development activity'
                    }
                ],
                'progress': 60
            }
        """
        try:
            logger.info(f"Analyzing TODO {todo_id} for smart updates")

            # Get TODO information
            todo = todo_db.get_user_todo(self.conn, todo_id)
            if not todo:
                raise ValueError(f"TODO {todo_id} not found")

            auto_suggestions = []
            confirm_suggestions = []

            # 1. Calculate progress from subtasks (auto-apply)
            progress = self.calculate_progress_from_subtasks(todo_id)
            if progress != todo.get('completion_percentage', 0):
                auto_suggestions.append({
                    'type': 'update_progress',
                    'data': {'percentage': progress},
                    'reason': f'Progress calculated from subtasks'
                })

            # 2. Get subtasks for completion detection
            subtasks = todo_db.get_user_todos(
                self.conn,
                parent_id=todo_id,
                limit=1000
            )

            # 3. Check if all subtasks are completed
            if subtasks and len(subtasks) > 0:
                all_completed = all(t['status'] == 'completed' for t in subtasks)
                if all_completed and todo['status'] != 'completed':
                    confirm_suggestions.append({
                        'type': 'mark_complete',
                        'confidence': 1.0,
                        'reason': f'All {len(subtasks)} subtasks are completed'
                    })

            # 4. Discover new subtasks from activities
            discovered_subtasks = await self._discover_subtasks_from_activities(todo_id, todo)
            for subtask in discovered_subtasks:
                confirm_suggestions.append({
                    'type': 'create_subtask',
                    'data': {
                        'title': subtask['title'],
                        'description': subtask.get('description', '')
                    },
                    'confidence': subtask.get('confidence', 0.7),
                    'reason': 'Discovered from recent activities'
                })

            # 5. AI-based completion detection (if no subtasks exist)
            if not subtasks or len(subtasks) == 0:
                completion_result = await self._ai_check_completion(todo_id, todo)
                if completion_result['should_complete'] and completion_result['confidence'] > 0.9:
                    confirm_suggestions.append({
                        'type': 'mark_complete',
                        'confidence': completion_result['confidence'],
                        'reason': completion_result['reason']
                    })

            logger.info(f"Generated {len(auto_suggestions)} auto-suggestions and {len(confirm_suggestions)} confirmation suggestions for TODO {todo_id}")

            return {
                'auto_suggestions': auto_suggestions,
                'confirm_suggestions': confirm_suggestions,
                'progress': progress
            }

        except Exception as e:
            logger.error(f"Error analyzing TODO {todo_id}: {e}", exc_info=True)
            raise

    async def apply_suggestions(self, todo_id: int, approved_suggestions: List[Dict]):
        """Apply user-approved suggestions.

        Args:
            todo_id: TODO ID
            approved_suggestions: List of approved suggestion dictionaries
        """
        try:
            logger.info(f"Applying {len(approved_suggestions)} suggestions to TODO {todo_id}")

            for suggestion in approved_suggestions:
                suggestion_type = suggestion.get('type')

                if suggestion_type == 'mark_complete':
                    # Mark TODO as completed
                    todo_db.update_user_todo(
                        self.conn,
                        todo_id,
                        status='completed',
                        completion_percentage=100
                    )
                    logger.info(f"Marked TODO {todo_id} as completed")

                elif suggestion_type == 'update_progress':
                    # Update progress percentage
                    percentage = suggestion['data']['percentage']
                    todo_db.update_user_todo(
                        self.conn,
                        todo_id,
                        completion_percentage=percentage
                    )
                    logger.info(f"Updated TODO {todo_id} progress to {percentage}%")

                elif suggestion_type == 'update_status':
                    # Update TODO status
                    new_status = suggestion['data']['status']
                    todo_db.update_user_todo(
                        self.conn,
                        todo_id,
                        status=new_status
                    )
                    logger.info(f"Updated TODO {todo_id} status to {new_status}")

                elif suggestion_type == 'create_subtask':
                    # Create new subtask
                    subtask_data = suggestion['data']
                    subtask_id = self.todo_manager.create_todo(
                        title=subtask_data['title'],
                        description=subtask_data.get('description'),
                        parent_id=todo_id
                    )
                    logger.info(f"Created subtask {subtask_id['id']} for TODO {todo_id}")

            logger.info(f"Successfully applied all suggestions to TODO {todo_id}")

        except Exception as e:
            logger.error(f"Error applying suggestions to TODO {todo_id}: {e}", exc_info=True)
            raise

    def calculate_progress_from_subtasks(self, todo_id: int) -> int:
        """Calculate progress based on subtask completion count.

        Args:
            todo_id: TODO ID

        Returns:
            Progress percentage (0-100)
        """
        try:
            # Get all subtasks
            subtasks = todo_db.get_user_todos(
                self.conn,
                parent_id=todo_id,
                limit=1000
            )

            if not subtasks or len(subtasks) == 0:
                # No subtasks, keep current progress
                todo = todo_db.get_user_todo(self.conn, todo_id)
                return todo.get('completion_percentage', 0) if todo else 0

            # Count completed subtasks
            total = len(subtasks)
            completed = len([t for t in subtasks if t['status'] == 'completed'])

            # Calculate percentage
            progress = int((completed / total) * 100)

            logger.debug(f"TODO {todo_id} progress: {completed}/{total} = {progress}%")

            return progress

        except Exception as e:
            logger.error(f"Error calculating progress for TODO {todo_id}: {e}")
            return 0

    async def _discover_subtasks_from_activities(
        self,
        todo_id: int,
        todo: Dict
    ) -> List[Dict]:
        """Discover new subtasks by analyzing recent activities with AI.

        Args:
            todo_id: TODO ID
            todo: TODO dictionary

        Returns:
            List of discovered subtasks with title, description, confidence
        """
        try:
            # Get recent activities
            activities = todo_db.get_todo_activities(self.conn, todo_id, limit=50)

            if not activities or len(activities) == 0:
                return []

            # Build activities timeline
            timeline = self._build_activities_timeline(activities)

            # Build AI prompt (will add to prompts.py later)
            prompt = f"""Analyze user's work activities to discover specific subtasks.

TODO Information:
- Title: {todo['title']}
- Description: {todo.get('description', 'No description')}

Recent Activities:
{timeline}

Requirements:
1. Identify if user is working on specific subtasks of this TODO
2. Extract concrete, actionable subtasks
3. Subtasks should be part of the main TODO, not new independent tasks
4. Keep subtask titles concise and clear

Return JSON format:
[
  {{
    "title": "Subtask title",
    "description": "Inferred from activities",
    "confidence": 0.85
  }},
  ...
]

Return empty array [] if no clear subtasks are detected.
"""

            # Call AI
            success, result, error = await self._call_ai_structured(prompt)

            if not success:
                logger.warning(f"AI subtask discovery failed for TODO {todo_id}: {error}")
                return []

            # Parse AI response
            subtasks = self._parse_subtasks_response(result)

            # Filter by confidence threshold
            discovered = [s for s in subtasks if s.get('confidence', 0) >= 0.7]

            logger.info(f"Discovered {len(discovered)} potential subtasks for TODO {todo_id}")

            return discovered

        except Exception as e:
            logger.error(f"Error discovering subtasks for TODO {todo_id}: {e}")
            return []

    async def _ai_check_completion(self, todo_id: int, todo: Dict) -> Dict:
        """Use AI to check if TODO should be marked as complete.

        Args:
            todo_id: TODO ID
            todo: TODO dictionary

        Returns:
            Dictionary with: {
                'should_complete': bool,
                'confidence': float,
                'reason': str
            }
        """
        try:
            # Get recent activities
            activities = todo_db.get_todo_activities(self.conn, todo_id, limit=50)

            if not activities or len(activities) == 0:
                return {'should_complete': False, 'confidence': 0.0, 'reason': 'No activities found'}

            # Get subtasks info
            subtasks = todo_db.get_user_todos(self.conn, parent_id=todo_id, limit=1000)
            subtasks_summary = f"{len(subtasks)} subtasks" if subtasks else "No subtasks"

            # Build timeline
            timeline = self._build_activities_timeline(activities)

            # Build AI prompt
            prompt = f"""Analyze if this TODO should be marked as completed.

TODO Information:
- Title: {todo['title']}
- Description: {todo.get('description', 'No description')}
- Subtasks: {subtasks_summary}

Recent Activities:
{timeline}

Determine if this TODO is completed.

Return JSON format:
{{
  "should_complete": true/false,
  "confidence": 0.95,
  "reason": "Brief explanation"
}}
"""

            # Call AI
            success, result, error = await self._call_ai_structured(prompt)

            if not success:
                return {'should_complete': False, 'confidence': 0.0, 'reason': error or 'AI call failed'}

            # Parse response
            completion_check = self._parse_completion_check(result)

            return completion_check

        except Exception as e:
            logger.error(f"Error checking completion for TODO {todo_id}: {e}")
            return {'should_complete': False, 'confidence': 0.0, 'reason': str(e)}

    def _build_activities_timeline(self, activities: List[Dict]) -> str:
        """Build formatted timeline text from activities.

        Args:
            activities: List of activity dictionaries

        Returns:
            Formatted timeline string
        """
        timeline_lines = []

        for activity in activities[:30]:  # Limit to most recent 30
            timestamp = activity.get('screenshot_timestamp', '')
            activity_type = activity.get('activity_type', 'general')
            description = activity.get('activity_description') or activity.get('screenshot_description', '')
            duration = activity.get('duration_minutes', 0)

            timeline_lines.append(f"[{timestamp}] ({activity_type}, {duration}min) {description}")

        return "\n".join(timeline_lines)

    async def _call_ai_structured(self, prompt: str) -> tuple:
        """Call AI service for structured JSON response.

        Args:
            prompt: Analysis prompt

        Returns:
            Tuple of (success, result, error)
        """
        try:
            from backend.config import settings

            if not settings.ai.enabled:
                return False, None, "AI service is not enabled"

            api_key = settings.openrouter_api_key or settings.openai_api_key
            if not api_key:
                return False, None, "No API key configured"

            try:
                from openai import OpenAI

                # Configure client based on provider
                if settings.ai.provider == "openrouter":
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://openrouter.ai/api/v1"
                    )
                else:
                    client = OpenAI(api_key=api_key)

                # Call AI with JSON mode request
                response = client.chat.completions.create(
                    model=settings.ai.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that returns structured JSON responses."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )

                # Extract response text
                response_text = response.choices[0].message.content

                return True, response_text, None

            except ImportError:
                return False, None, "OpenAI library not installed"
            except Exception as e:
                logger.error(f"AI API call error: {e}")
                return False, None, str(e)

        except Exception as e:
            logger.error(f"Error in _call_ai_structured: {e}")
            return False, None, str(e)

    def _parse_subtasks_response(self, response_text: str) -> List[Dict]:
        """Parse AI response for subtasks discovery.

        Args:
            response_text: AI response text

        Returns:
            List of subtask dictionaries
        """
        try:
            # Try to parse as JSON
            if isinstance(response_text, str):
                # Extract JSON from markdown code blocks if present
                import re
                json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

                subtasks = json.loads(response_text)
            else:
                subtasks = response_text

            # Validate structure
            if not isinstance(subtasks, list):
                logger.warning("Subtasks response is not a list")
                return []

            return subtasks

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse subtasks JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing subtasks response: {e}")
            return []

    def _parse_completion_check(self, response_text: str) -> Dict:
        """Parse AI response for completion check.

        Args:
            response_text: AI response text

        Returns:
            Dictionary with should_complete, confidence, reason
        """
        try:
            # Try to parse as JSON
            if isinstance(response_text, str):
                # Extract JSON from markdown code blocks if present
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

                result = json.loads(response_text)
            else:
                result = response_text

            # Validate structure
            return {
                'should_complete': result.get('should_complete', False),
                'confidence': result.get('confidence', 0.0),
                'reason': result.get('reason', '')
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse completion check JSON: {e}")
            return {'should_complete': False, 'confidence': 0.0, 'reason': 'JSON parse error'}
        except Exception as e:
            logger.error(f"Error parsing completion check: {e}")
            return {'should_complete': False, 'confidence': 0.0, 'reason': str(e)}
