"""Pattern recognition service for identifying work patterns and habits."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from loguru import logger

from backend.database import db


class PatternRecognitionService:
    """Recognize patterns in user work behavior."""

    def __init__(self):
        """Initialize pattern recognition service."""
        pass

    def identify_peak_hours(self, days: int = 7) -> List[Dict]:
        """Identify peak productivity hours.

        Args:
            days: Number of days to analyze

        Returns:
            List of peak hours with statistics
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            screenshots = db.get_screenshots(start_date=start_date, end_date=end_date, limit=10000)

            hourly_counts = defaultdict(lambda: {'count': 0, 'analyzed': 0})

            for screenshot in screenshots:
                hour = screenshot.timestamp.hour
                hourly_counts[hour]['count'] += 1
                if screenshot.analyzed:
                    hourly_counts[hour]['analyzed'] += 1

            # Calculate productivity score per hour
            peak_hours = []
            for hour, stats in hourly_counts.items():
                productivity = (stats['analyzed'] / stats['count']) if stats['count'] > 0 else 0
                peak_hours.append({
                    'hour': hour,
                    'total_screenshots': stats['count'],
                    'analyzed_screenshots': stats['analyzed'],
                    'productivity_rate': round(productivity * 100, 2)
                })

            # Sort by total screenshots (activity level)
            peak_hours.sort(key=lambda x: x['total_screenshots'], reverse=True)

            return peak_hours[:5]  # Top 5 peak hours

        except Exception as e:
            logger.error(f"Error identifying peak hours: {e}")
            return []

    def detect_repeated_activities(self, days: int = 7, min_occurrences: int = 3) -> List[Dict]:
        """Detect activities that are repeated frequently.

        Args:
            days: Number of days to analyze
            min_occurrences: Minimum number of occurrences to be considered repeated

        Returns:
            List of repeated activity patterns
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            screenshots = db.get_screenshots(start_date=start_date, end_date=end_date, limit=10000)

            # Track window titles and apps
            window_counter = Counter()
            app_counter = Counter()

            for screenshot in screenshots:
                if screenshot.window_title:
                    window_counter[screenshot.window_title] += 1
                if screenshot.app_name:
                    app_counter[screenshot.app_name] += 1

            # Find repeated patterns
            repeated_windows = [
                {'window': w, 'count': c}
                for w, c in window_counter.most_common(10)
                if c >= min_occurrences
            ]

            repeated_apps = [
                {'app': a, 'count': c}
                for a, c in app_counter.most_common(10)
                if c >= min_occurrences
            ]

            return {
                'repeated_windows': repeated_windows,
                'repeated_apps': repeated_apps,
                'analysis_period_days': days
            }

        except Exception as e:
            logger.error(f"Error detecting repeated activities: {e}")
            return {'repeated_windows': [], 'repeated_apps': [], 'analysis_period_days': days}

    def identify_context_switches(self, days: int = 7) -> Dict:
        """Identify frequent context switching patterns.

        Args:
            days: Number of days to analyze

        Returns:
            Context switching statistics
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            screenshots = db.get_screenshots(start_date=start_date, end_date=end_date, limit=10000)

            if len(screenshots) < 2:
                return {'average_switches_per_hour': 0, 'most_common_switches': []}

            screenshots.sort(key=lambda s: s.timestamp)

            switches = []
            previous_app = None

            for screenshot in screenshots:
                if screenshot.app_name and previous_app and screenshot.app_name != previous_app:
                    switches.append((previous_app, screenshot.app_name))
                previous_app = screenshot.app_name

            # Calculate switch frequency
            total_hours = (screenshots[-1].timestamp - screenshots[0].timestamp).total_seconds() / 3600
            avg_switches_per_hour = len(switches) / total_hours if total_hours > 0 else 0

            # Most common switch patterns
            switch_counter = Counter(switches)
            most_common = [
                {'from': s[0], 'to': s[1], 'count': c}
                for s, c in switch_counter.most_common(5)
            ]

            return {
                'average_switches_per_hour': round(avg_switches_per_hour, 2),
                'total_switches': len(switches),
                'most_common_switches': most_common,
                'analysis_period_days': days
            }

        except Exception as e:
            logger.error(f"Error identifying context switches: {e}")
            return {'average_switches_per_hour': 0, 'most_common_switches': []}

    def detect_work_rhythm(self, days: int = 7) -> Dict:
        """Detect user's work rhythm (when they start, peak, wind down).

        Args:
            days: Number of days to analyze

        Returns:
            Work rhythm analysis
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            screenshots = db.get_screenshots(start_date=start_date, end_date=end_date, limit=10000)

            # Group by date
            daily_data = defaultdict(lambda: {'first': None, 'last': None, 'count': 0})

            for screenshot in screenshots:
                date_key = screenshot.timestamp.date()
                if daily_data[date_key]['first'] is None or screenshot.timestamp < daily_data[date_key]['first']:
                    daily_data[date_key]['first'] = screenshot.timestamp
                if daily_data[date_key]['last'] is None or screenshot.timestamp > daily_data[date_key]['last']:
                    daily_data[date_key]['last'] = screenshot.timestamp
                daily_data[date_key]['count'] += 1

            # Calculate averages
            start_hours = []
            end_hours = []
            daily_durations = []

            for date, data in daily_data.items():
                if data['first'] and data['last']:
                    start_hours.append(data['first'].hour)
                    end_hours.append(data['last'].hour)
                    duration = (data['last'] - data['first']).total_seconds() / 3600
                    daily_durations.append(duration)

            if not start_hours:
                return {'message': 'Not enough data'}

            avg_start_hour = sum(start_hours) / len(start_hours)
            avg_end_hour = sum(end_hours) / len(end_hours)
            avg_duration = sum(daily_durations) / len(daily_durations)

            return {
                'average_start_hour': round(avg_start_hour, 1),
                'average_end_hour': round(avg_end_hour, 1),
                'average_work_duration_hours': round(avg_duration, 1),
                'days_analyzed': len(daily_data),
                'work_pattern': self._classify_work_pattern(avg_start_hour, avg_end_hour)
            }

        except Exception as e:
            logger.error(f"Error detecting work rhythm: {e}")
            return {'message': 'Error analyzing work rhythm'}

    def _classify_work_pattern(self, start_hour: float, end_hour: float) -> str:
        """Classify work pattern based on start and end times.

        Args:
            start_hour: Average start hour
            end_hour: Average end hour

        Returns:
            Work pattern classification
        """
        if start_hour < 7:
            return "Early Bird 🌅"
        elif start_hour < 9:
            return "Morning Person ☀️"
        elif start_hour < 12:
            return "Late Starter 🕐"
        elif end_hour > 22:
            return "Night Owl 🦉"
        elif end_hour > 18:
            return "Extended Hours 🌆"
        else:
            return "Standard Schedule 📅"

    def suggest_optimizations(self, days: int = 7) -> List[str]:
        """Generate optimization suggestions based on patterns.

        Args:
            days: Number of days to analyze

        Returns:
            List of actionable suggestions
        """
        try:
            suggestions = []

            # Check context switching
            switch_data = self.identify_context_switches(days)
            if switch_data['average_switches_per_hour'] > 10:
                suggestions.append(
                    "⚠️ High context switching detected. Consider time-blocking similar tasks together."
                )

            # Check work rhythm
            rhythm = self.detect_work_rhythm(days)
            if 'average_work_duration_hours' in rhythm:
                if rhythm['average_work_duration_hours'] > 10:
                    suggestions.append(
                        "⚠️ Long work hours detected. Remember to take breaks to maintain productivity."
                    )

            # Check peak hours
            peak_hours = self.identify_peak_hours(days)
            if peak_hours:
                top_hour = peak_hours[0]
                suggestions.append(
                    f"💡 Your peak productivity is around {top_hour['hour']}:00. Schedule important tasks during this time."
                )

            # Check repeated activities
            repeated = self.detect_repeated_activities(days)
            if len(repeated['repeated_windows']) > 3:
                suggestions.append(
                    "🔄 Multiple repeated activities detected. Consider creating shortcuts or automation for frequent tasks."
                )

            if not suggestions:
                suggestions.append("✅ Good work patterns! Keep maintaining your current workflow.")

            return suggestions

        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {e}")
            return ["Unable to generate suggestions at this time."]


# Global pattern recognition service instance
pattern_recognition_service = PatternRecognitionService()
