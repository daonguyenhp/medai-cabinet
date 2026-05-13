from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from models.schedule import ScheduleCreate, ScheduleResponse, DoseHistoryCreate, DoseHistoryResponse
from services.dynamodb import DynamoDBService

router = APIRouter()
logger = logging.getLogger(__name__)
db = DynamoDBService()


@router.get("/", response_model=List[ScheduleResponse])
async def list_schedules(user_id: str = Query(...)):
    try:
        return await db.list_schedules(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate):
    try:
        return await db.create_schedule(schedule.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str):
    try:
        await db.delete_schedule(schedule_id)
        return {"message": "Schedule deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/today", response_model=List[dict])
async def get_today_schedule(user_id: str = Query(...)):
    try:
        return await db.get_today_schedule(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dose-history", response_model=DoseHistoryResponse)
async def record_dose(dose: DoseHistoryCreate):
    try:
        return await db.record_dose(dose.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dose-history/list")
async def list_dose_history(user_id: str = Query(...), limit: int = Query(20)):
    try:
        return await db.list_dose_history(user_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
