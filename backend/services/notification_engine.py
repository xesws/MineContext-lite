"""Intelligent notification engine for proactive insights."""

from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List

from loguru import logger

from backend.database import db
from backend.services.pattern_recognition import pattern_recognition_service


class NotificationEngine:
    """Generate intelligent notifications and suggestions."""

    def __init__(self):
        """Initialize notification engine."""
        self.notification_rules = {
            'repeated_viewing': self._check_repeated_viewing,
            'long_session': self._check_long_session,
            'context_gap': self._check_context_gap,
            'new_project_detected': self._check_new_project,
            'low_productivity': self._check_low_productivity,
        }

    def generate_notifications(self, check_period_hours: int = 2) -> List[Dict]:
        """Generate all applicable notifications.

        Args:
            check_period_hours: Hours to look back for notification triggers

        Returns:
            List of notification dictionaries
        """
        notifications = []

        for rule_name, rule_func in self.notification_rules.items():
            try:
                notification = rule_func(check_period_hours)
                if notification:
                    notifications.append({
                        'type': rule_name,
                        'timestamp': datetime.now().isoformat(),
                        **notification
                    })
            except Exception as e:
                logger.error(f"Error in notification rule '{rule_name}': {e}")

        return notifications

    def _check_repeated_viewing(self, hours: int) -> Dict:
        """Check if user is viewing the same content repeatedly.

        Args:
            hours: Hours to check

        Returns:
            Notification dict or None
        """
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            screenshots = db.get_screenshots(start_date=cutoff, limit=100)

            if len(screenshots) < 3:
                return None

            # Count window titles
            window_counter = Counter()
            for screenshot in screenshots:
                if screenshot.window_title:
                    window_counter[screenshot.window_title] += 1

            # Find repeated items (>3 times in period)
            for window, count in window_counter.most_common(3):
                if count >= 3:
                    return {
                        'priority': 'medium',
                        'title': '🔄 Repeated Viewing Detected',
                        'message': f"You've viewed '{window}' {count} times in the last {hours} hours. Need help summarizing?",
                        'action': 'offer_summary',
                        'data': {'window_title': window, 'count': count}
                    }

            return None

        except Exception as e:
            logger.error(f"Error checking repeated viewing: {e}")
            return None

    def _check_long_session(self, hours: int) -> Dict:
        """Check for unusually long work sessions.

        Args:
            hours: Hours to check

        Returns:
            Notification dict or None
        """
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            screenshots = db.get_screenshots(start_date=cutoff, limit=200)

            if len(screenshots) < 10:
                return None

            # Check if continuous (gaps < 10 minutes)
            screenshots.sort(key=lambda s: s.timestamp)

            continuous_count = 1
            for i in range(1, len(screenshots)):
                gap = (screenshots[i].timestamp - screenshots[i-1].timestamp).total_seconds() / 60
                if gap < 10:
                    continuous_count += 1

            # If >80% of screenshots are continuous, it's a long session
            if continuous_count / len(screenshots) > 0.8:
                duration_hours = (screenshots[-1].timestamp - screenshots[0].timestamp).total_seconds() / 3600

                if duration_hours > 3:
                    return {
                        'priority': 'high',
                        'title': '⏰ Long Work Session',
                        'message': f"You've been working continuously for {duration_hours:.1f} hours. Time for a break?",
                        'action': 'suggest_break',
                        'data': {'duration_hours': duration_hours}
                    }

            return None

        except Exception as e:
            logger.error(f"Error checking long session: {e}")
            return None

    def _check_context_gap(self, hours: int) -> Dict:
        """Check for significant gaps in activity.

        Args:
            hours: Hours to check

        Returns:
            Notification dict or None
        """
        try:
            cutoff = datetime.now() - timedelta(hours=hours * 2)  # Look back 2x
            screenshots = db.get_screenshots(start_date=cutoff, limit=100)

            if len(screenshots) < 5:
                return None

            screenshots.sort(key=lambda s: s.timestamp)

            # Find largest gap
            max_gap = 0
            gap_start = None
            gap_end = None

            for i in range(1, len(screenshots)):
                gap = (screenshots[i].timestamp - screenshots[i-1].timestamp).total_seconds() / 60
                if gap > max_gap:
                    max_gap = gap
                    gap_start = screenshots[i-1].timestamp
                    gap_end = screenshots[i].timestamp

            # Notify if gap > 60 minutes in recent period
            if max_gap > 60:
                gap_hours = max_gap / 60

                return {
                    'priority': 'low',
                    'title': '📊 Activity Gap Detected',
                    'message': f"You had a {gap_hours:.1f} hour gap in activity. Session ended at {gap_start.strftime('%H:%M')}.",
                    'action': 'session_summary',
                    'data': {'gap_minutes': max_gap, 'gap_start': gap_start.isoformat()}
                }

            return None

        except Exception as e:
            logger.error(f"Error checking context gap: {e}")
            return None

    def _check_new_project(self, hours: int) -> Dict:
        """Detect if user started working on something new.

        Args:
            hours: Hours to check

        Returns:
            Notification dict or None
        """
        try:
            recent_cutoff = datetime.now() - timedelta(hours=hours)
            older_cutoff = datetime.now() - timedelta(days=7)

            recent_screenshots = db.get_screenshots(start_date=recent_cutoff, limit=50)
            older_screenshots = db.get_screenshots(
                start_date=older_cutoff,
                end_date=recent_cutoff,
                limit=200
            )

            if len(recent_screenshots) < 3:
                return None

            # Extract window keywords from recent
            recent_keywords = set()
            for screenshot in recent_screenshots:
                if screenshot.window_title:
                    words = screenshot.window_title.lower().split()
                    recent_keywords.update([w for w in words if len(w) > 4])

            # Extract from older
            older_keywords = set()
            for screenshot in older_screenshots:
                if screenshot.window_title:
                    words = screenshot.window_title.lower().split()
                    older_keywords.update([w for w in words if len(w) > 4])

            # Find new keywords (present in recent but not older)
            new_keywords = recent_keywords - older_keywords

            if len(new_keywords) > 3:
                sample_keywords = list(new_keywords)[:3]
                return {
                    'priority': 'medium',
                    'title': '🆕 New Project Detected',
                    'message': f"Detected new work: {', '.join(sample_keywords)}. Would you like to track this as a project?",
                    'action': 'create_project_tracker',
                    'data': {'keywords': list(new_keywords)}
                }

            return None

        except Exception as e:
            logger.error(f"Error checking new project: {e}")
            return None

    def _check_low_productivity(self, hours: int) -> Dict:
        """Check for below-average productivity.

        Args:
            hours: Hours to check

        Returns:
            Notification dict or None
        """
        try:
            from backend.services.activity_analyzer import activity_analyzer

            cutoff = datetime.now() - timedelta(hours=hours)
            summary = activity_analyzer.analyze_time_range(
                cutoff,
                datetime.now()
            )

            if summary['statistics']['total_screenshots'] < 10:
                return None

            productivity_score = summary['productivity_score']

            if productivity_score < 40:
                return {
                    'priority': 'medium',
                    'title': '📉 Productivity Alert',
                    'message': f"Productivity score is {productivity_score:.1f}/100 in the last {hours} hours. Consider focusing on core tasks.",
                    'action': 'productivity_tips',
                    'data': {'score': productivity_score}
                }

            return None

        except Exception as e:
            logger.error(f"Error checking productivity: {e}")
            return None

    def get_proactive_suggestions(self) -> List[str]:
        """Get proactive suggestions based on current context.

        Returns:
            List of suggestion strings
        """
        try:
            suggestions = []

            # Get pattern-based suggestions
            pattern_suggestions = pattern_recognition_service.suggest_optimizations(days=7)
            suggestions.extend(pattern_suggestions)

            # Check for pending TODOs
            pending_todos = db.get_todos(status='pending', limit=10)
            if len(pending_todos) > 5:
                suggestions.append(
                    f"📝 You have {len(pending_todos)} pending TODO items. Review and prioritize?"
                )

            # Check for unanalyzed screenshots
            all_screenshots = db.get_screenshots(limit=100)
            unanalyzed = [s for s in all_screenshots if not s.analyzed]
            if len(unanalyzed) > 10:
                suggestions.append(
                    f"🔍 {len(unanalyzed)} screenshots haven't been analyzed yet. Run batch analysis?"
                )

            return suggestions[:5]  # Top 5 suggestions

        except Exception as e:
            logger.error(f"Error generating proactive suggestions: {e}")
            return []


# Global notification engine instance
notification_engine = NotificationEngine()
