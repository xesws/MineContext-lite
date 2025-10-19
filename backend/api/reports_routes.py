"""Reports API routes for MineContext-v2."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from backend.database import db
from backend.services.report_generator import report_generator

router = APIRouter()


class ReportResponse(BaseModel):
    """Response model for generated reports."""
    report_id: Optional[int] = None
    content: str
    generated_at: str
    cached: bool = False


class ReportListItem(BaseModel):
    """Report list item."""
    id: int
    report_type: str
    period_start: str
    period_end: str
    generated_at: str


@router.post("/reports/daily", response_model=ReportResponse)
async def generate_daily_report(
    date: Optional[str] = Query(default=None, description="Date in YYYY-MM-DD format")
):
    """Generate a daily report.

    Args:
        date: Date string (YYYY-MM-DD). Defaults to today.

    Returns:
        Generated report in Markdown format
    """
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.now()

        result = await report_generator.generate_daily_report(target_date)

        return ReportResponse(
            report_id=result.get("report_id"),
            content=result["content"],
            generated_at=result.get("generated_at", datetime.now().isoformat()),
            cached=result.get("cached", False)
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/weekly", response_model=ReportResponse)
async def generate_weekly_report(
    start_date: Optional[str] = Query(default=None, description="Week start date (YYYY-MM-DD)")
):
    """Generate a weekly report.

    Args:
        start_date: Week start date. Defaults to current week.

    Returns:
        Generated report in Markdown format
    """
    try:
        if start_date:
            target_date = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # Default to start of current week (Monday)
            today = datetime.now()
            target_date = today - timedelta(days=today.weekday())

        result = await report_generator.generate_weekly_report(target_date)

        return ReportResponse(
            report_id=result.get("report_id"),
            content=result["content"],
            generated_at=result.get("generated_at", datetime.now().isoformat()),
            cached=result.get("cached", False)
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/list")
async def list_reports(
    report_type: Optional[str] = Query(default=None, description="Filter by type (daily/weekly)"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of reports")
):
    """List generated reports.

    Args:
        report_type: Filter by report type (optional)
        limit: Maximum number of reports to return

    Returns:
        List of reports
    """
    try:
        reports = db.get_reports(report_type=report_type, limit=limit)

        return {
            "reports": [
                ReportListItem(
                    id=r["id"],
                    report_type=r["report_type"],
                    period_start=r["period_start"],
                    period_end=r["period_end"],
                    generated_at=r["generated_at"]
                )
                for r in reports
            ],
            "total": len(reports)
        }

    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}")
async def get_report(report_id: int):
    """Get a specific report by ID.

    Args:
        report_id: Report ID

    Returns:
        Report content and metadata
    """
    try:
        # Query database directly for specific report
        from backend.database import db

        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM generated_reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Report not found")

            report = dict(row)

            return {
                "id": report["id"],
                "report_type": report["report_type"],
                "period_start": report["period_start"],
                "period_end": report["period_end"],
                "content": report["content"],
                "generated_at": report["generated_at"],
                "metadata": report.get("metadata")
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reports/{report_id}")
async def delete_report(report_id: int):
    """Delete a report.

    Args:
        report_id: Report ID

    Returns:
        Success status
    """
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM generated_reports WHERE id = ?", (report_id,))
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Report not found")

            return {
                "success": True,
                "message": f"Report {report_id} deleted successfully"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
