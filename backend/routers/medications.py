from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from models.medication import MedicationCreate, MedicationUpdate, MedicationResponse, DispenseRequest
from services.dynamodb import DynamoDBService
from services.aws_iot import IoTService

router = APIRouter()
logger = logging.getLogger(__name__)
db = DynamoDBService()
iot = IoTService()


@router.get("/", response_model=List[MedicationResponse])
async def list_medications(user_id: str = Query(...)):
    try:
        return await db.list_medications(user_id)
    except Exception as e:
        logger.error(f"Error listing medications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=MedicationResponse)
async def create_medication(medication: MedicationCreate):
    try:
        return await db.create_medication(medication.dict())
    except Exception as e:
        logger.error(f"Error creating medication: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{medication_id}", response_model=MedicationResponse)
async def get_medication(medication_id: str):
    med = await db.get_medication(medication_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    return med


@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication(medication_id: str, medication: MedicationUpdate):
    try:
        return await db.update_medication(medication_id, medication.dict(exclude_none=True))
    except Exception as e:
        logger.error(f"Error updating medication: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{medication_id}")
async def delete_medication(medication_id: str):
    try:
        await db.delete_medication(medication_id)
        return {"message": "Medication deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting medication: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{medication_id}/dispense")
async def dispense_medication(medication_id: str, request: DispenseRequest):
    try:
        med = await db.get_medication(medication_id)
        if not med:
            raise HTTPException(status_code=404, detail="Medication not found")
        if med.get("stock_count", 0) < request.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")

        # Send IoT command
        device_id = await db.get_user_device(med.get("user_id"))
        if device_id:
            await iot.send_dispense_command(
                device_id=device_id,
                slot=med.get("compartment", 1),
                quantity=request.quantity,
                medication_id=medication_id
            )

        # Optimistic stock update. Firmware will publish the real inventory via
        # telemetry after the dispense completes; iot.py will reconcile.
        new_stock = med.get("stock_count", 0) - request.quantity
        await db.update_medication(medication_id, {"stock_count": new_stock})

        return {"message": f"Dispensing {request.quantity} {med.get('unit', 'viên')}", "remaining": new_stock}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dispensing medication: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{medication_id}/sync-inventory")
async def sync_inventory_to_device(medication_id: str):
    """Push current stock_count to the firmware's inventory counter.

    Call this after refilling pills so the firmware knows the real count.
    """
    try:
        med = await db.get_medication(medication_id)
        if not med:
            raise HTTPException(status_code=404, detail="Medication not found")

        device_id = await db.get_user_device(med.get("user_id"))
        if not device_id:
            raise HTTPException(status_code=400, detail="User has no device")

        await iot.send_set_inventory(
            device_id=device_id,
            slot=med.get("compartment", 1),
            count=med.get("stock_count", 0),
        )
        return {"message": "Inventory synced to device",
                "slot": med.get("compartment"),
                "count": med.get("stock_count", 0)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))
