from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional
import logging
import json

from models.device import DeviceTelemetry, DeviceCommand, DispenseCommand
from services.dynamodb import DynamoDBService
from services.aws_iot import IoTService

router = APIRouter()
logger = logging.getLogger(__name__)
db = DynamoDBService()
iot = IoTService()

# WebSocket connections store
active_connections: dict = {}


@router.get("/")
async def list_devices(user_id: str = Query(...)):
    try:
        return await db.list_devices(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/telemetry")
async def get_latest_telemetry(device_id: str):
    try:
        return await db.get_latest_telemetry(device_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/telemetry/history")
async def get_telemetry_history(device_id: str, hours: int = Query(24)):
    try:
        return await db.get_telemetry_history(device_id, hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/command")
async def send_command(device_id: str, command: DeviceCommand):
    try:
        await iot.send_command(device_id, command.command_type, command.payload or {})
        return {"message": f"Command '{command.command_type}' sent to device {device_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/dispense")
async def dispense_from_device(device_id: str, command: DispenseCommand):
    try:
        await iot.send_dispense_command(
            device_id=device_id,
            compartment=command.compartment,
            quantity=command.quantity,
            medication_id=command.medication_id or "manual"
        )
        return {"message": f"Dispensing {command.quantity} from compartment {command.compartment}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/{device_id}/ws")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    await websocket.accept()
    active_connections[device_id] = websocket
    logger.info(f"WebSocket connected for device {device_id}")
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        active_connections.pop(device_id, None)
        logger.info(f"WebSocket disconnected for device {device_id}")
    except Exception as e:
        active_connections.pop(device_id, None)
        logger.error(f"WebSocket error: {e}")
