"""
AWS IoT Core service — publishes commands to ESP32 devices.

Two publish methods:
  1. boto3 iot-data (HTTP/REST) — uses IAM credentials (AWS_ACCESS_KEY_ID)
  2. MQTT over TLS — uses device certificates (IOT_CERT_PATH)

For the MedAI project we use method 1 (boto3) from the backend server,
and method 2 (MQTT/TLS) from the ESP32 firmware.

Topic convention (must match firmware config.h and IoT Policy):
  Device → Cloud:  medai/device/{device_id}/telemetry
  Device → Cloud:  medai/device/{device_id}/status
  Device → Cloud:  medai/device/{device_id}/heartbeat
  Cloud  → Device: medai/device/{device_id}/command
"""
import boto3
import json
import logging
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)

# ── Topic helpers ─────────────────────────────────────────────────────────────

def topic_command(device_id: str) -> str:
    return f"medai/device/{device_id}/command"

def topic_telemetry(device_id: str) -> str:
    return f"medai/device/{device_id}/telemetry"

def topic_status(device_id: str) -> str:
    return f"medai/device/{device_id}/status"


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

    async def send_command(self, device_id: str, command_type: str, payload: dict):
        """Publish a command to the device's command topic via IoT Data REST API."""
        topic = topic_command(device_id)
        message = {
            "command": command_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "backend",
        }
        try:
            self.client.publish(
                topic=topic,
                qos=1,
                payload=json.dumps(message),
            )
            logger.info(f"[IoT] Command '{command_type}' → {device_id} on {topic}")
        except Exception as e:
            logger.error(f"[IoT] publish error: {e}")
            raise

    async def send_dispense_command(
        self, device_id: str, compartment: int, quantity: int, medication_id: str
    ):
        """Open compartment to dispense pills."""
        await self.send_command(
            device_id=device_id,
            command_type="dispense",
            payload={
                "compartment": compartment,
                "quantity": quantity,
                "medication_id": medication_id,
            },
        )

    async def send_alert_command(self, device_id: str, alert_type: str, message: str):
        """Trigger buzzer/LED alert on the device."""
        await self.send_command(
            device_id=device_id,
            command_type="alert",
            payload={"alert_type": alert_type, "message": message},
        )

    async def request_telemetry(self, device_id: str):
        """Ask device to publish current telemetry immediately."""
        await self.send_command(device_id=device_id, command_type="get_telemetry", payload={})

    async def get_thing_shadow(self, device_id: str) -> dict:
        """Read the IoT Device Shadow (desired/reported state)."""
        try:
            response = self.client.get_thing_shadow(thingName=device_id)
            shadow = json.loads(response["payload"].read())
            return shadow.get("state", {})
        except Exception as e:
            logger.error(f"[IoT] get_thing_shadow error: {e}")
            return {}

    async def update_thing_shadow(self, device_id: str, desired: dict):
        """Update the desired state in IoT Device Shadow."""
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
