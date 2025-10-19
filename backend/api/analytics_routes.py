"""Analytics API routes for MineContext-v2."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from backend.services.activity_analyzer import activity_analyzer

router = APIRouter()


class TimeRangeRequest(BaseModel):
    """Request model for time range analysis."""
    start_time: str
    end_time: str


class TimeRangeResponse(BaseModel):
    """Response model for time range analysis."""
    period: dict
    statistics: dict
    activity_breakdown: dict
    app_usage: dict
    hourly_distribution: dict
    productivity_score: float
    sessions: list


class WorkPatternsResponse(BaseModel):
    """Response model for work patterns."""
    analysis_period_days: int
    most_productive_hours: list
    most_used_apps: dict
    average_session_duration_minutes: float
    total_sessions: int
    total_screenshots: int


@router.post("/analytics/time-range", response_model=TimeRangeResponse)
async def analyze_time_range(request: TimeRangeRequest):
    """Analyze activities within a time range.

    Args:
        request: Time range with start_time and end_time (ISO format)

    Returns:
        Comprehensive activity statistics
    """
    try:
        start_time = datetime.fromisoformat(request.start_time)
        end_time = datetime.fromisoformat(request.end_time)

        if start_time >= end_time:
            raise HTTPException(
                status_code=400,
                detail="start_time must be before end_time"
            )

        # Analyze the time range
        result = activity_analyzer.analyze_time_range(start_time, end_time)

        return TimeRangeResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid datetime format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error analyzing time range: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/daily")
async def get_daily_analytics(
    date: Optional[str] = Query(default=None, description="Date in YYYY-MM-DD format")
):
    """Get analytics for a specific day.

    Args:
        date: Date string (YYYY-MM-DD). Defaults to today.

    Returns:
        Daily analytics summary
    """
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.now()

        result = activity_analyzer.get_daily_summary(target_date)

        return result

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        logger.error(f"Error getting daily analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/weekly")
async def get_weekly_analytics(
    start_date: Optional[str] = Query(default=None, description="Week start date (YYYY-MM-DD)")
):
    """Get analytics for a week.

    Args:
        start_date: Week start date. Defaults to current week.

    Returns:
        Weekly analytics summary
    """
    try:
        if start_date:
            target_date = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # Default to start of current week (Monday)
            today = datetime.now()
            target_date = today - timedelta(days=today.weekday())

        result = activity_analyzer.get_weekly_summary(target_date)

        return result

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        logger.error(f"Error getting weekly analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/work-patterns", response_model=WorkPatternsResponse)
async def get_work_patterns(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze")
):
    """Identify work patterns over a period.

    Args:
        days: Number of days to analyze (1-90)

    Returns:
        Work pattern insights
    """
    try:
        result = activity_analyzer.identify_work_patterns(days)

        return WorkPatternsResponse(**result)

    except Exception as e:
        logger.error(f"Error getting work patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/productivity")
async def get_productivity_trend(
    days: int = Query(default=7, ge=1, le=30, description="Number of days")
):
    """Get productivity trend over time.

    Args:
        days: Number of days to analyze

    Returns:
        Daily productivity scores
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        daily_scores = []

        for i in range(days):
            date = start_date + timedelta(days=i)
            summary = activity_analyzer.get_daily_summary(date)

            daily_scores.append({
                "date": date.strftime("%Y-%m-%d"),
                "productivity_score": summary["productivity_score"],
                "total_screenshots": summary["statistics"]["total_screenshots"],
                "work_sessions": summary["statistics"]["work_sessions"]
            })

        return {
            "period_days": days,
            "daily_scores": daily_scores,
            "average_score": sum(d["productivity_score"] for d in daily_scores) / days if days > 0 else 0
        }

    except Exception as e:
        logger.error(f"Error getting productivity trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/aggregate-daily")
async def aggregate_daily_activities(
    date: str = Query(..., description="Date to aggregate (YYYY-MM-DD)")
):
    """Aggregate and store daily activity summaries.

    Args:
        date: Date string (YYYY-MM-DD)

    Returns:
        Success status
    """
    try:
        success = activity_analyzer.aggregate_daily_activities(date)

        if success:
            return {
                "success": True,
                "message": f"Activities aggregated for {date}"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to aggregate activities"
            )

    except Exception as e:
        logger.error(f"Error aggregating daily activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))
