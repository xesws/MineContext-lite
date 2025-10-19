"""Report generation service for MineContext-v2.

Generates structured reports using AI:
- Daily reports
- Weekly reports
- Project-specific reports
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from loguru import logger

from backend.config import settings
from backend.database import db
from backend.services.activity_analyzer import activity_analyzer


class ReportGenerator:
    """Generate intelligent reports using activity data and AI."""

    def __init__(self):
        """Initialize report generator."""
        pass

    async def generate_daily_report(self, date: datetime) -> Dict:
        """Generate a comprehensive daily report.

        Args:
            date: Date to generate report for

        Returns:
            Report dictionary with content and metadata
        """
        try:
            # Check if report already exists
            date_str = date.strftime("%Y-%m-%d")
            existing_report = db.get_report("daily", date_str)

            if existing_report:
                logger.info(f"Found existing daily report for {date_str}")
                return {
                    "report_id": existing_report["id"],
                    "content": existing_report["content"],
                    "generated_at": existing_report["generated_at"],
                    "cached": True
                }

            # Get activity summary
            summary = activity_analyzer.get_daily_summary(date)

            if summary["statistics"]["total_screenshots"] == 0:
                return {
                    "content": self._generate_no_data_report(date_str),
                    "cached": False
                }

            # Generate report content
            if settings.ai.enabled:
                content = await self._generate_ai_report(date_str, summary)
            else:
                content = self._generate_template_report(date_str, summary)

            # Save report
            report_id = db.save_report(
                report_type="daily",
                period_start=date_str,
                period_end=date_str,
                content=content,
                metadata=json.dumps(summary["statistics"])
            )

            return {
                "report_id": report_id,
                "content": content,
                "generated_at": datetime.now().isoformat(),
                "cached": False
            }

        except Exception as e:
            logger.error(f"Error generating daily report for {date}: {e}")
            return {
                "content": f"# Error Generating Report\n\nAn error occurred: {str(e)}",
                "error": str(e)
            }

    async def generate_weekly_report(self, start_date: datetime) -> Dict:
        """Generate a weekly report.

        Args:
            start_date: Start of the week

        Returns:
            Report dictionary
        """
        try:
            start_str = start_date.strftime("%Y-%m-%d")
            end_date = start_date + timedelta(days=7)
            end_str = end_date.strftime("%Y-%m-%d")

            # Check for existing report
            existing_report = db.get_report("weekly", start_str)
            if existing_report:
                return {
                    "report_id": existing_report["id"],
                    "content": existing_report["content"],
                    "generated_at": existing_report["generated_at"],
                    "cached": True
                }

            # Get weekly summary
            summary = activity_analyzer.analyze_time_range(start_date, end_date)

            if summary["statistics"]["total_screenshots"] == 0:
                return {
                    "content": self._generate_no_data_report(f"{start_str} to {end_str}"),
                    "cached": False
                }

            # Generate report
            if settings.ai.enabled:
                content = await self._generate_ai_weekly_report(start_str, end_str, summary)
            else:
                content = self._generate_template_weekly_report(start_str, end_str, summary)

            # Save report
            report_id = db.save_report(
                report_type="weekly",
                period_start=start_str,
                period_end=end_str,
                content=content,
                metadata=json.dumps(summary["statistics"])
            )

            return {
                "report_id": report_id,
                "content": content,
                "generated_at": datetime.now().isoformat(),
                "cached": False
            }

        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {
                "content": f"# Error Generating Report\n\nAn error occurred: {str(e)}",
                "error": str(e)
            }

    async def _generate_ai_report(self, date_str: str, summary: Dict) -> str:
        """Generate AI-powered daily report.

        Args:
            date_str: Date string
            summary: Activity summary

        Returns:
            Markdown report content
        """
        try:
            from backend.utils.ai_utils import get_vision_client

            # Construct prompt
            prompt = self._build_daily_report_prompt(date_str, summary)

            # Get AI client (non-vision, just text)
            client = get_vision_client()  # We'll use the same client infrastructure

            # For now, generate template report with AI enhancement later
            # TODO: Implement text-only LLM call for report generation
            return self._generate_template_report(date_str, summary)

        except Exception as e:
            logger.error(f"Error in AI report generation: {e}")
            return self._generate_template_report(date_str, summary)

    def _generate_template_report(self, date_str: str, summary: Dict) -> str:
        """Generate template-based daily report.

        Args:
            date_str: Date string
            summary: Activity summary

        Returns:
            Markdown report content
        """
        stats = summary["statistics"]
        activities = summary["activity_breakdown"]
        apps = summary["app_usage"]
        sessions = summary["sessions"]

        # Calculate top activity
        top_activity = max(activities, key=activities.get) if activities else "No activity"
        top_activity_count = activities.get(top_activity, 0)

        # Format time
        total_hours = summary["period"]["duration_seconds"] / 3600

        report = f"""# Daily Report - {date_str}

## 📊 Overview

- **Total Screenshots**: {stats['total_screenshots']}
- **Analyzed**: {stats['analyzed_screenshots']} ({stats['analysis_rate'] * 100:.1f}%)
- **Work Sessions**: {stats['work_sessions']}
- **Productivity Score**: {summary['productivity_score']:.1f}/100

## 🎯 Main Activities

"""

        # Activity breakdown
        for activity, count in sorted(activities.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_screenshots'] * 100) if stats['total_screenshots'] > 0 else 0
            report += f"- **{activity.capitalize()}**: {count} screenshots ({percentage:.1f}%)\n"

        report += "\n## 💻 Application Usage\n\n"

        # Top apps
        for app, count in list(apps.items())[:5]:
            report += f"- {app}: {count} screenshots\n"

        report += f"\n## ⏱️ Work Pattern\n\n"

        if sessions:
            total_session_time = sum(s['duration_seconds'] for s in sessions)
            avg_session = total_session_time / len(sessions)

            report += f"- **Total Active Time**: {total_session_time / 3600:.2f} hours\n"
            report += f"- **Average Session**: {avg_session / 60:.1f} minutes\n"
            report += f"- **App Switches**: {stats['app_switches']}\n"

        report += f"\n## 📈 Productivity Analysis\n\n"

        if summary['productivity_score'] >= 70:
            report += "✅ **Excellent productivity!** You maintained strong focus on productive tasks.\n"
        elif summary['productivity_score'] >= 50:
            report += "⚠️ **Good productivity** with room for improvement. Consider minimizing distractions.\n"
        else:
            report += "📉 **Low productivity detected.** Try to focus on core work activities.\n"

        report += f"\n## 🔍 Insights\n\n"

        # Add insights based on data
        if stats['app_switches'] > stats['total_screenshots'] * 0.3:
            report += "- ⚠️ High app switching detected. Consider batching similar tasks.\n"

        if "coding" in activities and activities["coding"] > stats['total_screenshots'] * 0.5:
            report += "- 💪 Strong focus on coding today!\n"

        if "communication" in activities and activities["communication"] > stats['total_screenshots'] * 0.3:
            report += "- 💬 Significant time spent on communication. Ensure it's productive collaboration.\n"

        report += f"\n---\n\n*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        return report

    def _generate_template_weekly_report(self, start_str: str, end_str: str, summary: Dict) -> str:
        """Generate template-based weekly report.

        Args:
            start_str: Start date string
            end_str: End date string
            summary: Weekly summary

        Returns:
            Markdown report content
        """
        stats = summary["statistics"]
        activities = summary["activity_breakdown"]
        apps = summary["app_usage"]

        report = f"""# Weekly Report - {start_str} to {end_str}

## 📊 Week Overview

- **Total Screenshots**: {stats['total_screenshots']}
- **Work Sessions**: {stats['work_sessions']}
- **Average Daily Screenshots**: {stats['total_screenshots'] / 7:.1f}
- **Average Productivity**: {summary['productivity_score']:.1f}/100

## 🎯 Activity Breakdown

"""

        for activity, count in sorted(activities.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_screenshots'] * 100) if stats['total_screenshots'] > 0 else 0
            report += f"- **{activity.capitalize()}**: {count} ({percentage:.1f}%)\n"

        report += f"\n## 💻 Top Applications\n\n"

        for i, (app, count) in enumerate(list(apps.items())[:10], 1):
            report += f"{i}. {app}: {count} screenshots\n"

        report += f"\n## 📈 Weekly Trends\n\n"

        if summary['productivity_score'] >= 70:
            report += "✅ **Excellent week!** Maintained high productivity throughout.\n"
        elif summary['productivity_score'] >= 50:
            report += "⚠️ **Decent week** but there's potential for optimization.\n"
        else:
            report += "📉 **Low productivity week.** Consider reviewing your workflow.\n"

        report += f"\n---\n\n*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        return report

    def _build_daily_report_prompt(self, date_str: str, summary: Dict) -> str:
        """Build prompt for AI daily report generation.

        Args:
            date_str: Date string
            summary: Activity summary

        Returns:
            Prompt string
        """
        return f"""Generate a professional daily work report for {date_str} based on the following data:

Statistics:
- Total Screenshots: {summary['statistics']['total_screenshots']}
- Work Sessions: {summary['statistics']['work_sessions']}
- Productivity Score: {summary['productivity_score']:.1f}/100

Activity Breakdown:
{json.dumps(summary['activity_breakdown'], indent=2)}

Application Usage:
{json.dumps(summary['app_usage'], indent=2)}

Please generate a Markdown report with the following sections:
## 📊 Overview
## 🎯 Main Activities
## 💻 Application Usage
## ⏱️ Work Pattern
## 📈 Productivity Analysis
## 🔍 Insights
## ✅ Recommendations

Keep the tone professional and data-driven. Focus on actionable insights.
"""

    def _generate_no_data_report(self, period: str) -> str:
        """Generate report for periods with no data.

        Args:
            period: Period description

        Returns:
            Markdown report
        """
        return f"""# Report - {period}

## No Data Available

No screenshots or activities were recorded for this period.

This could mean:
- Capture was not running
- No active work during this time
- Data was not analyzed yet

Try starting the capture service and ensure screenshots are being analyzed.

---

*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    async def _generate_ai_weekly_report(self, start_str: str, end_str: str, summary: Dict) -> str:
        """Generate AI-powered weekly report.

        Args:
            start_str: Start date
            end_str: End date
            summary: Weekly summary

        Returns:
            Markdown report
        """
        # TODO: Implement AI-powered weekly report
        return self._generate_template_weekly_report(start_str, end_str, summary)


# Global report generator instance
report_generator = ReportGenerator()
