"""
IoT Router — receives data forwarded by AWS IoT Core Rules Engine.

Firmware (medai-esp32) publishes on these topics:
  medai/device/{id}/telemetry   → {device, inventory: {slot1, slot2, slot3}}
  medai/device/{id}/status      → {device, status: "dispensing"|"completed"|"failed"|"pong"|"online"|"inventory_updated"}
  medai/device/{id}/alert       → {device, alert: "jam"|"not_picked_up"|"inventory_low"|..., detail}

IoT Rules forward these to the endpoints below.
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Optional
import logging
from datetime import datetime

from services.dynamodb import DynamoDBService
from services.sns_service import SNSService
from config import settings
from boto3.dynamodb.conditions import Attr, Key

router = APIRouter()
logger = logging.getLogger(__name__)
db = DynamoDBService()
sns = SNSService()


# ── Telemetry ingestion (called by IoT Rule) ──────────────────────────────────

@router.post("/telemetry")
async def ingest_telemetry(request: Request):
    """
    Receives telemetry from firmware via AWS IoT Rule.

    Firmware payload:
      {"device": "medai-001", "inventory": {"slot1": 10, "slot2": 8, "slot3": 5}}

    We:
      1. Store raw telemetry (for history / debugging)
      2. Reconcile medication.stock_count with firmware's inventory per slot
    """
    try:
        payload = await request.json()
        device_id = payload.get("device") or payload.get("device_id")
        if not device_id:
            raise HTTPException(status_code=400, detail="Missing device field")

        # Normalize: store as device_id for DynamoDB key
        payload["device_id"] = device_id
        if not payload.get("timestamp"):
            payload["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # TTL: keep 7 days
        payload["ttl"] = int(datetime.utcnow().timestamp()) + 7 * 86400

        # Store raw telemetry
        table = db._table(settings.DYNAMODB_TELEMETRY_TABLE)
        table.put_item(Item=payload)

        # Reconcile inventory with backend medication records
        inventory = payload.get("inventory") or {}
        if inventory:
            await _reconcile_inventory(device_id, inventory)

        logger.info(f"Telemetry stored for device {device_id}: inventory={inventory}")
        return {"status": "ok", "device_id": device_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telemetry ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/status")
async def ingest_status(request: Request):
    """
    Receives status from firmware.

    Firmware payload:
      {"device": "medai-001", "status": "dispensing"|"completed"|"failed"|"pong"|"online"|"inventory_updated"}
    """
    try:
        payload = await request.json()
        device_id = payload.get("device") or payload.get("device_id")
        status = payload.get("status")
        if not device_id:
            raise HTTPException(status_code=400, detail="Missing device field")

        logger.info(f"Device {device_id} status: {status}")

        # Surface failed dispenses as alerts
        user = await _get_user_by_device(device_id)
        if user and status == "failed":
            await db.create_alert({
                "user_id": user["user_id"],
                "medication_id": None,
                "alert_type": "dispense_failed",
                "severity": "warning",
                "title": "Dispense thất bại",
                "message": "Thiết bị báo dispense thất bại. Kiểm tra ngay.",
            })

        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alert")
async def ingest_alert(request: Request):
    """
    Receives alert from firmware (jam, not_picked_up, inventory_low, invalid_slot, ...).

    Firmware payload:
      {"device": "medai-001", "alert": "jam", "detail": "..."}
    """
    try:
        payload = await request.json()
        device_id = payload.get("device") or payload.get("device_id")
        alert_type = payload.get("alert", "unknown")
        detail = payload.get("detail", "")
        if not device_id:
            raise HTTPException(status_code=400, detail="Missing device field")

        user = await _get_user_by_device(device_id)
        if not user:
            logger.warning(f"Alert from unknown device {device_id}")
            return {"status": "ignored"}

        # Map firmware alert types → user-facing Vietnamese messages
        title, message, severity = _format_device_alert(alert_type, detail)

        alert = await db.create_alert({
            "user_id": user["user_id"],
            "medication_id": None,
            "alert_type": f"device_{alert_type}",
            "severity": severity,
            "title": title,
            "message": message,
        })

        # Notify caregiver for high/critical alerts
        if severity in ("high", "critical"):
            await sns.notify_caregiver(
                user_id=user["user_id"],
                subject=title,
                message=message,
            )

        logger.info(f"Alert from {device_id}: {alert_type} → {alert['alert_id']}")
        return {"status": "ok", "alert_id": alert["alert_id"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alert ingestion error: {e}")
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

async def _reconcile_inventory(device_id: str, inventory: dict):
    """
    Sync firmware inventory → backend medication.stock_count.

    Firmware is the source of truth for physical pill count (it detects
    dispenses via IR). Backend updates stock_count to match.
    """
    try:
        user = await _get_user_by_device(device_id)
        if not user:
            return

        medications = await db.list_medications(user["user_id"])
        for med in medications:
            compartment = med.get("compartment")
            if compartment is None:
                continue
            key = f"slot{compartment}"
            new_count = inventory.get(key)
            if new_count is None:
                continue
            # Normalize to int (DynamoDB returns Decimal)
            new_count = int(new_count)
            current = int(med.get("stock_count", 0))
            if new_count != current:
                await db.update_medication(
                    med["medication_id"],
                    {"stock_count": new_count},
                )
                logger.info(
                    f"Reconciled {med['name']} (slot {compartment}): "
                    f"{current} → {new_count}"
                )
    except Exception as e:
        logger.error(f"Inventory reconcile error: {e}")


def _format_device_alert(alert_type: str, detail: str):
    """Map firmware alert type → (title, message, severity)."""
    mapping = {
        "jam": (
            "Tủ thuốc bị kẹt",
            "🚨 Cơ cấu phát thuốc bị kẹt sau nhiều lần thử. Kiểm tra khay thuốc ngay.",
            "high",
        ),
        "not_picked_up": (
            "Chưa lấy thuốc",
            "⚠️ Thuốc đã được phát nhưng không có ai lấy trong 30 giây.",
            "medium",
        ),
        "inventory_low": (
            "Hết thuốc trong tủ",
            "⚠️ Ngăn thuốc không đủ số lượng yêu cầu. Cần nạp thêm.",
            "medium",
        ),
        "invalid_slot": (
            "Lệnh không hợp lệ",
            f"Lỗi lệnh dispense: {detail}",
            "low",
        ),
        "invalid_quantity": (
            "Số lượng không hợp lệ",
            f"Số lượng dispense phải từ 1-10. Detail: {detail}",
            "low",
        ),
        "parse_error": (
            "Lỗi lệnh từ backend",
            f"Thiết bị không parse được lệnh: {detail}",
            "low",
        ),
        "unknown_command": (
            "Lệnh không xác định",
            f"Thiết bị nhận lệnh không biết: {detail}",
            "low",
        ),
    }
    return mapping.get(alert_type, (
        f"Cảnh báo thiết bị: {alert_type}",
        f"Chi tiết: {detail}",
        "medium",
    ))


async def _get_user_by_device(device_id: str) -> dict | None:
    """Scan users table to find user linked to device_id."""
    try:
        table = db._table(settings.DYNAMODB_USERS_TABLE)
        resp = table.scan(FilterExpression=Attr("device_id").eq(device_id))
        items = resp.get("Items", [])
        return items[0] if items else None
    except Exception as e:
        logger.error(f"_get_user_by_device error: {e}")
        return None
