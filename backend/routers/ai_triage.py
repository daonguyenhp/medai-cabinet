from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging

from services.ai_triage_service import AITriageService
from services.dynamodb import DynamoDBService

router = APIRouter()
logger = logging.getLogger(__name__)
triage_service = AITriageService()
db = DynamoDBService()


class TriageRequest(BaseModel):
    user_id: str
    symptoms: str


class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_history: Optional[List[dict]] = None


@router.get("/quick-check/{user_id}")
async def quick_check(user_id: str):
    try:
        medications = await db.list_medications(user_id)
        expired = []
        near_expiry = []
        low_stock = []

        for med in medications:
            status = med.get("expiry_status")
            if status == "expired":
                expired.append({"name": med["name"], "days_overdue": abs(med.get("days_until_expiry", 0))})
            elif status in ["warning", "critical"]:
                near_expiry.append({"name": med["name"], "days_remaining": med.get("days_until_expiry", 0)})
            if med.get("stock_count", 0) <= med.get("low_stock_threshold", 5):
                low_stock.append({"name": med["name"], "remaining": med.get("stock_count", 0), "unit": med.get("unit", "viên")})

        return {
            "total_medications": len(medications),
            "expired": expired,
            "near_expiry": near_expiry,
            "low_stock": low_stock,
            "needs_attention": len(expired) + len(near_expiry) + len(low_stock)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_symptoms(request: TriageRequest):
    try:
        medications = await db.list_medications(request.user_id)
        result = await triage_service.analyze_symptoms(
            symptoms=request.symptoms,
            available_medications=medications
        )
        return result
    except Exception as e:
        logger.error(f"Triage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Pull current medication list so the AI can answer with real data
        # without forcing the user to list pills manually.
        medications = await db.list_medications(request.user_id)
        result = await triage_service.chat(
            message=request.message,
            conversation_history=request.conversation_history or [],
            available_medications=medications,
        )
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/refill-suggestions/{user_id}")
async def refill_suggestions(user_id: str):
    """
    AI-powered shopping list:
    Estimates which meds are low/expiring/running out based on dose history,
    and asks the LLM to draft a friendly summary in Vietnamese.
    """
    try:
        medications = await db.list_medications(user_id)
        # Pull a generous slice of recent dose history for usage estimation
        dose_history = await db.list_dose_history(user_id, limit=200)
        result = await triage_service.suggest_refills(
            medications=medications,
            dose_history=dose_history,
        )
        return result
    except Exception as e:
        logger.error(f"Refill suggestions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
