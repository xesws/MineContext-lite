"""Activity analysis service for MineContext-v2.

Analyzes user activities from screenshots to provide:
- Time-range activity statistics
- Work pattern recognition
- Productivity metrics
- Session detection
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from loguru import logger

from backend.database import db


class ActivityAnalyzer:
    """Analyze user activities and generate insights."""

    def __init__(self):
        """Initialize activity analyzer."""
        self.gap_threshold_minutes = 30  # Gap between sessions

    def analyze_time_range(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """Analyze activities within a time range.

        Args:
            start_time: Start of analysis period
            end_time: End of analysis period

        Returns:
            Dictionary containing comprehensive statistics
        """
        try:
            # Get screenshots in time range
            screenshots = db.get_screenshots(
                start_date=start_time,
                end_date=end_time,
                limit=10000
            )

            if not screenshots:
                return self._empty_stats()

            # Calculate basic metrics
            total_screenshots = len(screenshots)
            analyzed_count = sum(1 for s in screenshots if s.analyzed)

            # Activity breakdown
            activity_breakdown = Counter()
            app_usage = Counter()
            hourly_distribution = defaultdict(int)
            app_switching_count = 0
            previous_app = None

            for screenshot in screenshots:
                # Get activities for this screenshot
                activities = db.get_activities_by_screenshot(screenshot.id)

                for activity in activities:
                    activity_breakdown[activity.activity_type] += 1

                # Track app usage
                if screenshot.app_name:
                    app_usage[screenshot.app_name] += 1

                    # Count app switches
                    if previous_app and previous_app != screenshot.app_name:
                        app_switching_count += 1
                    previous_app = screenshot.app_name

                # Hourly distribution
                hour = screenshot.timestamp.hour
                hourly_distribution[hour] += 1

            # Calculate productivity score
            productivity_score = self._calculate_productivity_score(
                screenshots,
                activity_breakdown,
                app_switching_count
            )

            # Detect work sessions
            sessions = self._detect_work_sessions(screenshots)

            # Calculate duration
            duration_seconds = int((end_time - start_time).total_seconds())

            return {
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "duration_seconds": duration_seconds
                },
                "statistics": {
                    "total_screenshots": total_screenshots,
                    "analyzed_screenshots": analyzed_count,
                    "analysis_rate": analyzed_count / total_screenshots if total_screenshots > 0 else 0,
                    "app_switches": app_switching_count,
                    "work_sessions": len(sessions)
                },
                "activity_breakdown": dict(activity_breakdown),
                "app_usage": dict(app_usage.most_common(10)),
                "hourly_distribution": dict(hourly_distribution),
                "productivity_score": productivity_score,
                "sessions": sessions
            }

        except Exception as e:
            logger.error(f"Error analyzing time range: {e}")
            return self._empty_stats()

    def _detect_work_sessions(self, screenshots: List) -> List[Dict]:
        """Detect work sessions from screenshots.

        Sessions are periods of continuous activity (gaps < threshold).

        Args:
            screenshots: List of screenshot objects

        Returns:
            List of session dictionaries
        """
        if not screenshots:
            return []

        # Sort by timestamp
        sorted_screenshots = sorted(screenshots, key=lambda s: s.timestamp)

        sessions = []
        current_session_shots = [sorted_screenshots[0]]

        for i in range(1, len(sorted_screenshots)):
            current = sorted_screenshots[i]
            previous = sorted_screenshots[i - 1]

            gap_minutes = (current.timestamp - previous.timestamp).total_seconds() / 60

            if gap_minutes < self.gap_threshold_minutes:
                current_session_shots.append(current)
            else:
                # End current session, start new one
                if current_session_shots:
                    sessions.append(self._create_session_summary(current_session_shots))
                current_session_shots = [current]

        # Add final session
        if current_session_shots:
            sessions.append(self._create_session_summary(current_session_shots))

        return sessions

    def _create_session_summary(self, screenshots: List) -> Dict:
        """Create summary for a work session.

        Args:
            screenshots: List of screenshots in the session

        Returns:
            Session summary dictionary
        """
        if not screenshots:
            return {}

        start_time = screenshots[0].timestamp
        end_time = screenshots[-1].timestamp
        duration_seconds = int((end_time - start_time).total_seconds())

        # Get activity types
        activity_types = Counter()
        for screenshot in screenshots:
            activities = db.get_activities_by_screenshot(screenshot.id)
            for activity in activities:
                activity_types[activity.activity_type] += 1

        dominant_activity = activity_types.most_common(1)[0][0] if activity_types else "unknown"

        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration_seconds,
            "screenshot_count": len(screenshots),
            "dominant_activity": dominant_activity,
            "activity_breakdown": dict(activity_types)
        }

    def _calculate_productivity_score(
        self,
        screenshots: List,
        activity_breakdown: Counter,
        app_switches: int
    ) -> float:
        """Calculate productivity score (0-100).

        Factors:
        - Productive activity ratio (coding, writing): 40%
        - Focus (low app switching): 30%
        - Activity diversity (balanced work): 20%
        - Screenshot density: 10%

        Args:
            screenshots: List of screenshots
            activity_breakdown: Activity type counts
            app_switches: Number of app switches

        Returns:
            Productivity score (0-100)
        """
        if not screenshots:
            return 0.0

        total_activities = sum(activity_breakdown.values())
        if total_activities == 0:
            return 0.0

        # Productive activities
        productive_activities = ["coding", "writing", "designing", "data"]
        productive_count = sum(activity_breakdown.get(act, 0) for act in productive_activities)
        productive_ratio = productive_count / total_activities
        productive_score = productive_ratio * 40

        # Focus score (inverse of app switching frequency)
        avg_switch_per_screenshot = app_switches / len(screenshots) if len(screenshots) > 0 else 0
        # Assume 1 switch per 10 screenshots is good
        focus_score = max(0, 30 - (avg_switch_per_screenshot * 3))

        # Diversity score (balanced activities)
        activity_entropy = self._calculate_entropy(list(activity_breakdown.values()))
        diversity_score = min(activity_entropy * 10, 20)

        # Density score (screenshots per hour)
        if len(screenshots) >= 2:
            time_span_hours = (screenshots[-1].timestamp - screenshots[0].timestamp).total_seconds() / 3600
            screenshots_per_hour = len(screenshots) / time_span_hours if time_span_hours > 0 else 0
            # Assume 60 screenshots/hour (1 per minute) is optimal
            density_score = min(screenshots_per_hour / 6, 10)
        else:
            density_score = 0

        total_score = productive_score + focus_score + diversity_score + density_score

        return round(min(total_score, 100), 2)

    def _calculate_entropy(self, values: List[int]) -> float:
        """Calculate Shannon entropy of a distribution.

        Args:
            values: List of counts

        Returns:
            Entropy value
        """
        import math

        total = sum(values)
        if total == 0:
            return 0.0

        entropy = 0.0
        for value in values:
            if value > 0:
                p = value / total
                entropy -= p * math.log2(p)

        return entropy

    def get_daily_summary(self, date: datetime) -> Dict:
        """Get summary for a specific day.

        Args:
            date: Date to analyze

        Returns:
            Daily summary dictionary
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        return self.analyze_time_range(start_of_day, end_of_day)

    def get_weekly_summary(self, start_date: datetime) -> Dict:
        """Get summary for a week.

        Args:
            start_date: Start of the week

        Returns:
            Weekly summary dictionary
        """
        end_date = start_date + timedelta(days=7)
        return self.analyze_time_range(start_date, end_date)

    def calculate_app_category(self, app_name: str) -> str:
        """Categorize application by name.

        Args:
            app_name: Application name

        Returns:
            Category string
        """
        app_name_lower = app_name.lower() if app_name else ""

        if any(term in app_name_lower for term in ["vscode", "vim", "pycharm", "intellij", "code", "sublime", "atom"]):
            return "development"
        elif any(term in app_name_lower for term in ["chrome", "firefox", "safari", "edge", "browser"]):
            return "browsing"
        elif any(term in app_name_lower for term in ["slack", "teams", "zoom", "skype", "discord", "mail"]):
            return "communication"
        elif any(term in app_name_lower for term in ["figma", "photoshop", "illustrator", "sketch", "design"]):
            return "design"
        elif any(term in app_name_lower for term in ["word", "docs", "notion", "obsidian", "note"]):
            return "documentation"
        elif any(term in app_name_lower for term in ["terminal", "iterm", "cmd", "powershell"]):
            return "terminal"
        else:
            return "other"

    def aggregate_daily_activities(self, date: str) -> bool:
        """Aggregate activities for a day and store in database.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            True if successful
        """
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            summary = self.get_daily_summary(date_obj)

            # Store each activity type
            for activity_type, count in summary["activity_breakdown"].items():
                # Calculate approximate duration (assume each screenshot represents 5 seconds)
                total_seconds = count * 5

                # Create app breakdown JSON
                app_breakdown = json.dumps(summary["app_usage"])

                # Upsert summary
                db.upsert_activity_summary(
                    date=date,
                    activity_type=activity_type,
                    total_seconds=total_seconds,
                    screenshot_count=count,
                    app_breakdown=app_breakdown
                )

            logger.info(f"Aggregated activities for {date}")
            return True

        except Exception as e:
            logger.error(f"Error aggregating daily activities for {date}: {e}")
            return False

    def identify_work_patterns(self, days: int = 7) -> Dict:
        """Identify work patterns over a period.

        Args:
            days: Number of days to analyze

        Returns:
            Work pattern insights
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        screenshots = db.get_screenshots(start_date=start_date, end_date=end_date, limit=10000)

        if not screenshots:
            return {"message": "No data available"}

        # Most productive hours
        hourly_counts = defaultdict(int)
        for screenshot in screenshots:
            hourly_counts[screenshot.timestamp.hour] += 1

        most_productive_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        # Most used apps
        app_counts = Counter()
        for screenshot in screenshots:
            if screenshot.app_name:
                app_counts[screenshot.app_name] += 1

        # Average session duration
        sessions = self._detect_work_sessions(screenshots)
        if sessions:
            avg_session_duration = sum(s["duration_seconds"] for s in sessions) / len(sessions)
        else:
            avg_session_duration = 0

        return {
            "analysis_period_days": days,
            "most_productive_hours": [{"hour": h, "activity_count": c} for h, c in most_productive_hours],
            "most_used_apps": dict(app_counts.most_common(5)),
            "average_session_duration_minutes": round(avg_session_duration / 60, 2),
            "total_sessions": len(sessions),
            "total_screenshots": len(screenshots)
        }

    def _empty_stats(self) -> Dict:
        """Return empty statistics structure.

        Returns:
            Empty stats dictionary
        """
        return {
            "period": {"start": None, "end": None, "duration_seconds": 0},
            "statistics": {
                "total_screenshots": 0,
                "analyzed_screenshots": 0,
                "analysis_rate": 0,
                "app_switches": 0,
                "work_sessions": 0
            },
            "activity_breakdown": {},
            "app_usage": {},
            "hourly_distribution": {},
            "productivity_score": 0.0,
            "sessions": []
        }


# Global activity analyzer instance
activity_analyzer = ActivityAnalyzer()
