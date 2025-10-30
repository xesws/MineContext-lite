"""TaskDecomposer service - AI-powered task decomposition into subtasks."""

import json
import re
from typing import Dict, List, Optional

from loguru import logger


class TaskDecomposer:
    """Service for decomposing tasks into subtasks using AI."""

    async def decompose_task(
        self,
        title: str,
        description: Optional[str] = None,
        estimated_hours: Optional[float] = None
    ) -> List[Dict]:
        """Decompose a task into concrete subtasks using AI.

        Args:
            title: Task title
            description: Detailed task description
            estimated_hours: Estimated hours to complete the main task

        Returns:
            List of subtask dictionaries:
            [
                {
                    'title': 'Design database schema',
                    'description': 'Define tables and relationships',
                    'estimated_hours': 2.0,
                    'priority': 'high'
                },
                ...
            ]
        """
        try:
            logger.info(f"Decomposing task: {title}")

            # Build AI prompt
            prompt = self._build_decomposition_prompt(title, description, estimated_hours)

            # Call AI
            success, result, error = await self._call_ai_structured(prompt)

            if not success:
                logger.error(f"AI decomposition failed: {error}")
                return []

            # Parse AI response
            subtasks = self._parse_subtasks_response(result)

            # Validate and clean subtasks
            validated_subtasks = self._validate_subtasks(subtasks, title, estimated_hours)

            logger.info(f"Successfully decomposed task into {len(validated_subtasks)} subtasks")

            return validated_subtasks

        except Exception as e:
            logger.error(f"Error decomposing task '{title}': {e}", exc_info=True)
            return []

    def _build_decomposition_prompt(
        self,
        title: str,
        description: Optional[str],
        estimated_hours: Optional[float]
    ) -> str:
        """Build AI prompt for task decomposition.

        Args:
            title: Task title
            description: Task description
            estimated_hours: Estimated hours

        Returns:
            Formatted prompt string
        """
        desc_text = description if description else "No detailed description provided"
        hours_text = f"{estimated_hours} hours" if estimated_hours else "Not specified"

        prompt = f"""Please decompose the following task into 3-7 concrete, actionable subtasks:

Task Title: {title}
Task Description: {desc_text}
Estimated Time: {hours_text}

Requirements:
1. Each subtask should be specific, measurable, and completable
2. Subtasks should follow a logical order
3. Estimate time required for each subtask (in hours)
4. Assign priority level: high, medium, or low
5. If total time is specified, subtask times should roughly sum to that total
6. Subtasks should be parts of the main task, not independent tasks

Return JSON format:
[
  {{
    "title": "Subtask title (concise, action-oriented)",
    "description": "Brief explanation of what needs to be done",
    "estimated_hours": 2.0,
    "priority": "high"
  }},
  ...
]

Return a JSON array of 3-7 subtasks.
"""

        return prompt

    async def _call_ai_structured(self, prompt: str) -> tuple:
        """Call AI service for structured JSON response.

        Args:
            prompt: Task decomposition prompt

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
                        {
                            "role": "system",
                            "content": "You are a helpful task planning assistant that decomposes complex tasks into actionable subtasks. Always return valid JSON arrays."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
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
        """Parse AI response to extract subtasks.

        Args:
            response_text: AI response text

        Returns:
            List of subtask dictionaries
        """
        try:
            # Try to parse as JSON
            if isinstance(response_text, str):
                # Extract JSON from markdown code blocks if present
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
            logger.debug(f"Response text: {response_text}")
            return []
        except Exception as e:
            logger.error(f"Error parsing subtasks response: {e}")
            return []

    def _validate_subtasks(
        self,
        subtasks: List[Dict],
        main_title: str,
        total_estimated_hours: Optional[float]
    ) -> List[Dict]:
        """Validate and clean subtask data.

        Args:
            subtasks: Raw subtasks from AI
            main_title: Main task title for context
            total_estimated_hours: Total estimated hours

        Returns:
            Validated and cleaned subtasks
        """
        validated = []

        for i, subtask in enumerate(subtasks):
            try:
                # Ensure required fields exist
                if not subtask.get('title'):
                    logger.warning(f"Subtask {i} missing title, skipping")
                    continue

                # Clean and validate each field
                cleaned = {
                    'title': str(subtask['title']).strip()[:200],  # Max 200 chars
                    'description': str(subtask.get('description', '')).strip()[:500],  # Max 500 chars
                    'estimated_hours': self._validate_hours(subtask.get('estimated_hours')),
                    'priority': self._validate_priority(subtask.get('priority', 'medium'))
                }

                validated.append(cleaned)

            except Exception as e:
                logger.warning(f"Error validating subtask {i}: {e}")
                continue

        # Limit to 3-7 subtasks
        if len(validated) < 3:
            logger.warning(f"Only {len(validated)} subtasks generated, expected 3-7")
        elif len(validated) > 7:
            logger.warning(f"Too many subtasks ({len(validated)}), limiting to 7")
            validated = validated[:7]

        # Adjust time estimates if total is specified
        if total_estimated_hours and len(validated) > 0:
            validated = self._adjust_time_estimates(validated, total_estimated_hours)

        return validated

    def _validate_hours(self, hours_value) -> Optional[float]:
        """Validate estimated hours value.

        Args:
            hours_value: Raw hours value

        Returns:
            Validated hours as float or None
        """
        try:
            if hours_value is None or hours_value == '':
                return None

            hours = float(hours_value)

            # Ensure reasonable range (0.5 to 100 hours per subtask)
            if hours < 0.5:
                return 0.5
            elif hours > 100:
                return 100.0

            # Round to 1 decimal place
            return round(hours, 1)

        except (ValueError, TypeError):
            return None

    def _validate_priority(self, priority_value) -> str:
        """Validate priority value.

        Args:
            priority_value: Raw priority value

        Returns:
            Validated priority: 'low', 'medium', or 'high'
        """
        priority = str(priority_value).lower().strip()

        if priority in ['low', 'medium', 'high']:
            return priority

        # Default to medium
        return 'medium'

    def _adjust_time_estimates(
        self,
        subtasks: List[Dict],
        total_hours: float
    ) -> List[Dict]:
        """Adjust subtask time estimates to match total.

        Args:
            subtasks: List of subtasks with estimated_hours
            total_hours: Target total hours

        Returns:
            Subtasks with adjusted time estimates
        """
        try:
            # Calculate current total
            subtask_total = sum(
                s.get('estimated_hours', 0) or 0
                for s in subtasks
            )

            # If subtasks have no time estimates, distribute evenly
            if subtask_total == 0:
                hours_per_subtask = round(total_hours / len(subtasks), 1)
                for subtask in subtasks:
                    subtask['estimated_hours'] = hours_per_subtask
                return subtasks

            # If subtasks total is close to target (within 20%), keep as is
            if 0.8 <= (subtask_total / total_hours) <= 1.2:
                return subtasks

            # Otherwise, scale proportionally
            scale_factor = total_hours / subtask_total

            for subtask in subtasks:
                if subtask.get('estimated_hours'):
                    scaled_hours = subtask['estimated_hours'] * scale_factor
                    subtask['estimated_hours'] = round(scaled_hours, 1)

            logger.debug(f"Adjusted subtask times: {subtask_total}h -> {total_hours}h (scale: {scale_factor:.2f})")

            return subtasks

        except Exception as e:
            logger.warning(f"Error adjusting time estimates: {e}")
            return subtasks
