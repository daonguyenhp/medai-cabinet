from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from services.dynamodb import DynamoDBService
from services.expiry_service import ExpiryService

router = APIRouter()
logger = logging.getLogger(__name__)
db = DynamoDBService()
expiry_service = ExpiryService()


@router.get("/")
async def list_alerts(user_id: str = Query(...), resolved: Optional[bool] = None):
    try:
        return await db.list_alerts(user_id, resolved)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_count(user_id: str = Query(...)):
    try:
        alerts = await db.list_alerts(user_id, resolved=False)
        return {"count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    try:
        await db.resolve_alert(alert_id)
        return {"message": "Alert resolved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/resolve-all")
async def resolve_all_alerts(user_id: str = Query(...)):
    try:
        alerts = await db.list_alerts(user_id, resolved=False)
        for alert in alerts:
            await db.resolve_alert(alert["alert_id"])
        return {"resolved_count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-medications")
async def check_medications(user_id: str = Query(...)):
    try:
        medications = await db.list_medications(user_id)
        alerts_created = 0

        for med in medications:
            new_alerts = await expiry_service.check_and_create_alerts(user_id, med)
            alerts_created += len(new_alerts)

        return {"medications_checked": len(medications), "alerts_created": alerts_created}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
