from fastapi import APIRouter, HTTPException, Query
import logging
from datetime import datetime, timedelta

from services.dynamodb import DynamoDBService

router = APIRouter()
logger = logging.getLogger(__name__)
db = DynamoDBService()


@router.get("/summary")
async def get_dashboard_summary(user_id: str = Query(...)):
    """Get dashboard summary: medication stats, today's schedule, recent alerts."""
    try:
        medications = await db.list_medications(user_id)
        today_schedule = await db.get_today_schedule(user_id)
        alerts = await db.list_alerts(user_id, resolved=False)
        telemetry = None

        # Get device telemetry if user has a device
        user = await db.get_user(user_id)
        if user and user.get("device_id"):
            try:
                telemetry = await db.get_latest_telemetry(user["device_id"])
            except Exception:
                pass

        # Compute stats
        total_meds = len(medications)
        expired_count = sum(1 for m in medications if m.get("expiry_status") == "expired")
        near_expiry_count = sum(1 for m in medications if m.get("expiry_status") in ["warning", "critical"])
        low_stock_count = sum(1 for m in medications if m.get("stock_count", 0) <= m.get("low_stock_threshold", 5))

        taken_today = sum(1 for s in today_schedule if s.get("status") == "taken")
        pending_today = sum(1 for s in today_schedule if s.get("status") == "pending")

        return {
            "medications": {
                "total": total_meds,
                "expired": expired_count,
                "near_expiry": near_expiry_count,
                "low_stock": low_stock_count,
            },
            "today_schedule": {
                "total": len(today_schedule),
                "taken": taken_today,
                "pending": pending_today,
                "items": today_schedule[:5],  # Show first 5
            },
            "alerts": {
                "unread": len(alerts),
                "recent": alerts[:3],
            },
            "device": telemetry,
        }
    except Exception as e:
        logger.error(f"Dashboard summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/adherence")
async def get_adherence_stats(user_id: str = Query(...), days: int = Query(7)):
    """Get medication adherence statistics for the past N days."""
    try:
        history = await db.list_dose_history(user_id, limit=200)
        cutoff = datetime.utcnow() - timedelta(days=days)

        recent = [h for h in history if h.get("taken_time") and
                  datetime.fromisoformat(h["taken_time"].replace("Z", "")) >= cutoff]

        total = len(recent)
        taken = sum(1 for h in recent if h.get("status") == "taken")
        missed = sum(1 for h in recent if h.get("status") == "missed")
        late = sum(1 for h in recent if h.get("status") == "late")

        adherence_rate = round((taken / total * 100) if total > 0 else 0, 1)

        return {
            "period_days": days,
            "total_doses": total,
            "taken": taken,
            "missed": missed,
            "late": late,
            "adherence_rate": adherence_rate,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
