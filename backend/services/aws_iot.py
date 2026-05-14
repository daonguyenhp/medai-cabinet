"""
AWS IoT Core service — publishes commands to ESP32 devices.

Command format must match firmware (medai-esp32):
  {"command": "dispense",      "slot": 1, "quantity": 2}
  {"command": "set_inventory", "slot": 1, "count": 10}
  {"command": "ping"}

Topic convention (must match firmware config.h and IoT Policy):
  Device → Cloud:  medai/device/{device_id}/telemetry   (inventory)
  Device → Cloud:  medai/device/{device_id}/status      (dispensing/completed/failed/pong)
  Device → Cloud:  medai/device/{device_id}/alert       (jam/not_picked_up/inventory_low/...)
  Cloud  → Device: medai/device/{device_id}/command
"""
import boto3
import json
import logging

from config import settings

logger = logging.getLogger(__name__)


# ── Topic helpers ─────────────────────────────────────────────────────────────

def topic_command(device_id: str) -> str:
    return f"medai/device/{device_id}/command"


def topic_telemetry(device_id: str) -> str:
    return f"medai/device/{device_id}/telemetry"


def topic_status(device_id: str) -> str:
    return f"medai/device/{device_id}/status"


def topic_alert(device_id: str) -> str:
    return f"medai/device/{device_id}/alert"


class IoTService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "iot-data",
                region_name=settings.AWS_REGION,
                endpoint_url=f"https://{settings.IOT_ENDPOINT}" if settings.IOT_ENDPOINT else None,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
                aws_session_token=settings.AWS_SESSION_TOKEN or None,
            )
        return self._client

    async def _publish(self, device_id: str, message: dict):
        """Publish raw command JSON to the device's command topic."""
        topic = topic_command(device_id)
        try:
            self.client.publish(
                topic=topic,
                qos=1,
                payload=json.dumps(message),
            )
            logger.info(f"[IoT] → {device_id} on {topic}: {message}")
        except Exception as e:
            logger.error(f"[IoT] publish error: {e}")
            raise

    # ── Commands matching firmware (medai-esp32) ──────────────────────────────

    async def send_dispense_command(
        self, device_id: str, slot: int, quantity: int, medication_id: str = ""
    ):
        """Open compartment to dispense pills.

        Firmware expects: {"command": "dispense", "slot": 1-3, "quantity": 1-10}
        `medication_id` is ignored by firmware but kept for backend logging.
        """
        if medication_id:
            logger.info(f"[IoT] Dispense for medication_id={medication_id}")
        await self._publish(device_id, {
            "command": "dispense",
            "slot": slot,
            "quantity": quantity,
        })

    async def send_set_inventory(self, device_id: str, slot: int, count: int):
        """Sync pill count from backend → firmware after refill.

        Firmware expects: {"command": "set_inventory", "slot": 1-3, "count": N}
        """
        await self._publish(device_id, {
            "command": "set_inventory",
            "slot": slot,
            "count": count,
        })

    async def send_ping(self, device_id: str):
        """Ping the device — firmware replies with status='pong'."""
        await self._publish(device_id, {"command": "ping"})

    # ── Generic command passthrough (kept for backwards compatibility) ────────

    async def send_command(self, device_id: str, command_type: str, payload: dict):
        """
        Generic command sender.

        For `dispense` and `set_inventory`, flattens payload to match firmware.
        For unknown commands, sends as-is (useful for future extensions).
        """
        payload = payload or {}

        if command_type == "dispense":
            await self.send_dispense_command(
                device_id=device_id,
                slot=payload.get("slot") or payload.get("compartment", 1),
                quantity=payload.get("quantity", 1),
                medication_id=payload.get("medication_id", ""),
            )
        elif command_type == "set_inventory":
            await self.send_set_inventory(
                device_id=device_id,
                slot=payload.get("slot", 1),
                count=payload.get("count", 0),
            )
        elif command_type == "ping":
            await self.send_ping(device_id)
        else:
            # Unknown command — send as-is
            message = {"command": command_type, **payload}
            await self._publish(device_id, message)

    # ── Device Shadow (optional, kept for future use) ─────────────────────────

    async def get_thing_shadow(self, device_id: str) -> dict:
        try:
            response = self.client.get_thing_shadow(thingName=device_id)
            shadow = json.loads(response["payload"].read())
            return shadow.get("state", {})
        except Exception as e:
            logger.error(f"[IoT] get_thing_shadow error: {e}")
            return {}

    async def update_thing_shadow(self, device_id: str, desired: dict):
        payload = {"state": {"desired": desired}}
        try:
            self.client.update_thing_shadow(
                thingName=device_id,
                payload=json.dumps(payload),
            )
            logger.info(f"[IoT] Shadow updated for {device_id}: {desired}")
        except Exception as e:
            logger.error(f"[IoT] update_thing_shadow error: {e}")
            raise
