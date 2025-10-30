"""ProgressAnalyzer service - AI-driven TODO progress analysis."""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from loguru import logger

from todolist.backend import database as todo_db
from todolist.config.prompts import PROGRESS_ANALYSIS_PROMPT


class ProgressAnalyzer:
    """Service for analyzing TODO progress using AI."""

    def __init__(self, db_connection: sqlite3.Connection, cache_hours: int = 24):
        """Initialize ProgressAnalyzer.

        Args:
            db_connection: SQLite database connection
            cache_hours: Hours to cache analysis results
        """
        self.conn = db_connection
        self.cache_hours = cache_hours

    async def analyze_todo_progress(
        self,
        todo_id: int,
        force_reanalysis: bool = False
    ) -> Dict:
        """Analyze TODO progress using AI.

        Args:
            todo_id: TODO ID to analyze
            force_reanalysis: Force new analysis even if recent cache exists

        Returns:
            Progress analysis dictionary with:
            - completed_aspects: List of completed items
            - remaining_aspects: List of remaining items
            - completion_percentage: 0-100
            - summary: AI-generated summary
            - next_steps: Recommended actions
            - total_time_spent: Minutes
            - analyzed_at: Timestamp
        """
        try:
            # 1. Check for recent cached analysis
            if not force_reanalysis:
                recent_snapshot = self._get_recent_snapshot(todo_id)
                if recent_snapshot:
                    logger.info(f"Using cached progress analysis for TODO {todo_id}")
                    return self._format_snapshot_response(recent_snapshot)

            # 2. Get TODO information
            todo = todo_db.get_user_todo(self.conn, todo_id)
            if not todo:
                raise ValueError(f"TODO {todo_id} not found")

            # 3. Get activity timeline
            activities = self.get_activity_timeline(todo_id)

            if not activities:
                logger.warning(f"No activities found for TODO {todo_id}")
                return self._create_empty_progress(todo_id, todo)

            # 4. Build timeline text for AI
            timeline_text = self._build_timeline_text(activities)

            # 5. Construct AI prompt
            prompt = PROGRESS_ANALYSIS_PROMPT.format(
                todo_title=todo['title'],
                todo_description=todo['description'] or "无详细描述",
                activities_timeline=timeline_text
            )

            # 6. Call AI analysis
            logger.info(f"Calling AI for progress analysis of TODO {todo_id}")
            success, result, error = await self._call_ai_analysis(prompt)

            if not success:
                logger.error(f"AI analysis failed for TODO {todo_id}: {error}")
                return {
                    'error': error or 'AI analysis failed',
                    'todo_id': todo_id,
                    'completion_percentage': todo.get('completion_percentage', 0)
                }

            # 7. Parse AI response
            analysis = self._parse_ai_response(result)

            # 8. Calculate total time spent
            total_time = self.calculate_total_time(todo_id)

            # 9. Save progress snapshot
            snapshot_id = todo_db.create_progress_snapshot(
                conn=self.conn,
                todo_id=todo_id,
                completed_aspects=analysis.get('completed_aspects', []),
                remaining_aspects=analysis.get('remaining_aspects', []),
                total_time_spent=total_time,
                ai_summary=analysis.get('summary', ''),
                completion_percentage=analysis.get('completion_percentage', 0),
                next_steps=analysis.get('next_steps', [])
            )

            logger.info(f"Saved progress snapshot {snapshot_id} for TODO {todo_id}")

            # 10. Update TODO completion percentage
            todo_db.update_user_todo(
                self.conn,
                todo_id,
                completion_percentage=analysis.get('completion_percentage', 0)
            )

            # 11. Return complete analysis
            return {
                'todo_id': todo_id,
                'completed_aspects': analysis.get('completed_aspects', []),
                'remaining_aspects': analysis.get('remaining_aspects', []),
                'completion_percentage': analysis.get('completion_percentage', 0),
                'summary': analysis.get('summary', ''),
                'next_steps': analysis.get('next_steps', []),
                'total_time_spent': total_time,
                'analyzed_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing TODO {todo_id} progress: {e}", exc_info=True)
            return {
                'error': str(e),
                'todo_id': todo_id,
                'completion_percentage': 0
            }

    def get_activity_timeline(self, todo_id: int) -> List[Dict]:
        """Get activity timeline for a TODO with screenshot details.

        Args:
            todo_id: TODO ID

        Returns:
            List of activity dictionaries with screenshot information
        """
        return todo_db.get_todo_activities(self.conn, todo_id, limit=None)

    def _build_timeline_text(self, activities: List[Dict]) -> str:
        """Build formatted timeline text for AI analysis.

        Args:
            activities: List of activity dictionaries

        Returns:
            Formatted timeline string
        """
        if not activities:
            return "无活动记录"

        timeline_lines = []

        for i, activity in enumerate(activities, 1):
            # Format timestamp
            timestamp = activity.get('screenshot_timestamp') or activity.get('matched_at')
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except:
                    pass

            time_str = timestamp.strftime("%Y-%m-%d %H:%M") if isinstance(timestamp, datetime) else str(timestamp)

            # Get activity details
            duration = activity.get('duration_minutes', 0)
            activity_type = activity.get('activity_type', 'general')
            description = activity.get('activity_description') or activity.get('screenshot_description', '无描述')

            # Format activity entry
            timeline_lines.append(
                f"{i}. [{time_str}] {self._translate_activity_type(activity_type)}（{duration}分钟）\n"
                f"   内容：{description}"
            )

        return "\n\n".join(timeline_lines)

    def _translate_activity_type(self, activity_type: str) -> str:
        """Translate activity type to Chinese.

        Args:
            activity_type: Activity type in English

        Returns:
            Chinese translation
        """
        translations = {
            'reading': '阅读',
            'coding': '编程',
            'video': '观看视频',
            'browsing': '浏览网页',
            'communication': '沟通交流',
            'design': '设计',
            'general': '一般活动'
        }
        return translations.get(activity_type, activity_type)

    def calculate_total_time(self, todo_id: int) -> int:
        """Calculate total time spent on a TODO.

        Args:
            todo_id: TODO ID

        Returns:
            Total time in minutes
        """
        return todo_db.calculate_total_time_spent(self.conn, todo_id)

    def _get_recent_snapshot(self, todo_id: int) -> Optional[Dict]:
        """Get recent progress snapshot if within cache time.

        Args:
            todo_id: TODO ID

        Returns:
            Snapshot dictionary or None
        """
        snapshot = todo_db.get_latest_progress_snapshot(self.conn, todo_id)

        if not snapshot:
            return None

        # Check if snapshot is recent enough
        analyzed_at = snapshot.get('analyzed_at')
        if isinstance(analyzed_at, str):
            try:
                analyzed_at = datetime.fromisoformat(analyzed_at)
            except:
                return None

        if isinstance(analyzed_at, datetime):
            age = datetime.now() - analyzed_at
            if age < timedelta(hours=self.cache_hours):
                return snapshot

        return None

    def _format_snapshot_response(self, snapshot: Dict) -> Dict:
        """Format snapshot data into response format.

        Args:
            snapshot: Snapshot dictionary from database

        Returns:
            Formatted response dictionary
        """
        return {
            'todo_id': snapshot['todo_id'],
            'completed_aspects': json.loads(snapshot.get('completed_aspects', '[]')),
            'remaining_aspects': json.loads(snapshot.get('remaining_aspects', '[]')),
            'completion_percentage': snapshot.get('completion_percentage', 0),
            'summary': snapshot.get('ai_summary', ''),
            'next_steps': json.loads(snapshot.get('next_steps', '[]')),
            'total_time_spent': snapshot.get('total_time_spent', 0),
            'analyzed_at': snapshot.get('analyzed_at', datetime.now().isoformat())
        }

    def _create_empty_progress(self, todo_id: int, todo: Dict) -> Dict:
        """Create empty progress response when no activities exist.

        Args:
            todo_id: TODO ID
            todo: TODO dictionary

        Returns:
            Empty progress dictionary
        """
        return {
            'todo_id': todo_id,
            'completed_aspects': [],
            'remaining_aspects': [],
            'completion_percentage': todo.get('completion_percentage', 0),
            'summary': '暂无活动记录，无法生成进度分析',
            'next_steps': ['开始进行相关活动', '记录学习或工作过程'],
            'total_time_spent': 0,
            'analyzed_at': datetime.now().isoformat()
        }

    async def _call_ai_analysis(self, prompt: str) -> tuple:
        """Call AI service for progress analysis.

        Args:
            prompt: Analysis prompt

        Returns:
            Tuple of (success, result, error)
        """
        try:
            from backend.config import settings

            # Use OpenRouter/OpenAI for text-only completion
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

                # Call AI with text-only prompt
                response = client.chat.completions.create(
                    model=settings.ai.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )

                # Extract response text
                response_text = response.choices[0].message.content

                # Return in expected format
                result = {"description": response_text}
                return True, result, None

            except ImportError:
                return False, None, "openai package not installed"
            except Exception as e:
                logger.error(f"Error calling AI API: {e}")
                return False, None, str(e)

        except Exception as e:
            logger.error(f"Error calling AI analysis: {e}")
            return False, None, str(e)

    def _parse_ai_response(self, result: Dict) -> Dict:
        """Parse AI response and extract structured data.

        Args:
            result: AI response dictionary

        Returns:
            Parsed analysis dictionary
        """
        try:
            # AI response should be in result['description']
            response_text = result.get('description', '')

            # Try to parse as JSON
            try:
                analysis = json.loads(response_text)
                logger.debug("Successfully parsed AI response as JSON")
                return analysis
            except json.JSONDecodeError:
                # Try to extract JSON from text
                logger.warning("AI response not valid JSON, attempting to extract")
                return self._extract_json_from_text(response_text)

        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return {
                'completed_aspects': [],
                'remaining_aspects': [],
                'completion_percentage': 0,
                'summary': '解析AI响应失败',
                'next_steps': []
            }

    def _extract_json_from_text(self, text: str) -> Dict:
        """Try to extract JSON from text response.

        Args:
            text: Response text

        Returns:
            Extracted dictionary or empty structure
        """
        # Try to find JSON block in text
        import re

        # Look for JSON-like structure
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                parsed = json.loads(match)
                if 'completed_aspects' in parsed or 'completion_percentage' in parsed:
                    return parsed
            except:
                continue

        # If no valid JSON found, return default
        return {
            'completed_aspects': [],
            'remaining_aspects': [],
            'completion_percentage': 0,
            'summary': text[:100] if text else '无分析结果',
            'next_steps': []
        }
