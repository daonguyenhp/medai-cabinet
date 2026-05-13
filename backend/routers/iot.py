"""
IoT Router — receives data forwarded by AWS IoT Core Rules Engine.

IoT Rule SQL:
  SELECT * FROM 'medai/device/+/telemetry'
  → POST https://api/api/v1/iot/telemetry

  SELECT * FROM 'medai/device/+/status'
  → POST https://api/api/v1/iot/status
"""
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import logging
from datetime import datetime

from services.dynamodb import DynamoDBService
from services.sns_service import SNSService
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)
db = DynamoDBService()
sns = SNSService()


# ── Telemetry ingestion (called by IoT Rule) ──────────────────────────────────

@router.post("/telemetry")
async def ingest_telemetry(request: Request):
    """
    Receives telemetry forwarded by AWS IoT Core Rule:
      SELECT * FROM 'medai/device/+/telemetry'
    Stores in DynamoDB and checks for environment alerts.
    """
    try:
        payload = await request.json()
        device_id = payload.get("device_id")
        if not device_id:
            raise HTTPException(status_code=400, detail="Missing device_id")

        # Add server-side timestamp if missing
        if not payload.get("timestamp"):
            payload["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Add TTL (keep 7 days of telemetry)
        payload["ttl"] = int(datetime.utcnow().timestamp()) + 7 * 86400

        # Store telemetry
        table = db._table(settings.DYNAMODB_TELEMETRY_TABLE)
        table.put_item(Item=payload)

        # Check environment thresholds and alert if needed
        await _check_environment_alerts(device_id, payload)

        logger.info(f"Telemetry stored for device {device_id}")
        return {"status": "ok", "device_id": device_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telemetry ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/status")
async def ingest_status(request: Request):
    """
    Receives device status/heartbeat forwarded by IoT Rule:
      SELECT * FROM 'medai/device/+/status'
    Updates device online/offline state.
    """
    try:
        payload = await request.json()
        device_id = payload.get("device_id")
        if not device_id:
            raise HTTPException(status_code=400, detail="Missing device_id")

        logger.info(f"Status update from device {device_id}: online={payload.get('online')}")
        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def iot_webhook(request: Request):
    """Generic IoT webhook — fallback for any IoT Rule action."""
    try:
        payload = await request.json()
        logger.info(f"IoT webhook: {payload}")
        return {"status": "received"}
    except Exception as e:
        logger.error(f"IoT webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _check_environment_alerts(device_id: str, telemetry: dict):
    """Check temperature, humidity, battery and create alerts if thresholds exceeded."""
    try:
        # Find user linked to this device
        user = await _get_user_by_device(device_id)
        if not user:
            return

        user_id = user["user_id"]
        temp    = telemetry.get("temperature")
        humidity = telemetry.get("humidity")
        battery  = telemetry.get("battery_level")

        alerts_to_create = []

        if temp is not None and temp > settings.TEMP_MAX:
            alerts_to_create.append({
                "user_id": user_id,
                "medication_id": None,
                "alert_type": "high_temperature",
                "severity": "warning",
                "title": "Nhiệt độ tủ thuốc cao",
                "message": f"🌡️ Nhiệt độ tủ thuốc đang là {temp:.1f}°C (ngưỡng: {settings.TEMP_MAX}°C). Kiểm tra ngay!",
            })

        if humidity is not None and humidity > settings.HUMIDITY_MAX:
            alerts_to_create.append({
                "user_id": user_id,
                "medication_id": None,
                "alert_type": "high_humidity",
                "severity": "warning",
                "title": "Độ ẩm tủ thuốc cao",
                "message": f"💧 Độ ẩm tủ thuốc đang là {humidity:.1f}% (ngưỡng: {settings.HUMIDITY_MAX}%). Kiểm tra ngay!",
            })

        if battery is not None and battery < settings.BATTERY_LOW:
            alerts_to_create.append({
                "user_id": user_id,
                "medication_id": None,
                "alert_type": "low_battery",
                "severity": "warning" if battery > 10 else "critical",
                "title": "Pin thiết bị yếu",
                "message": f"🔋 Pin thiết bị còn {battery}%. Vui lòng sạc pin.",
            })

        for alert_data in alerts_to_create:
            await db.create_alert(alert_data)
            # Notify caregiver via SNS for critical alerts
            if alert_data["severity"] == "critical":
                await sns.notify_caregiver(
                    user_id=user_id,
                    subject=alert_data["title"],
                    message=alert_data["message"],
                )

    except Exception as e:
        logger.error(f"Environment alert check error: {e}")


async def _get_user_by_device(device_id: str) -> dict | None:
    """Scan users table to find user linked to device_id."""
    try:
        from boto3.dynamodb.conditions import Attr
        table = db._table(settings.DYNAMODB_USERS_TABLE)
        resp = table.scan(FilterExpression=Attr("device_id").eq(device_id))
        items = resp.get("Items", [])
        return items[0] if items else None
    except Exception as e:
        logger.error(f"_get_user_by_device error: {e}")
        return None
