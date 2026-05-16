"""
MQTT Subscriber — listens to device topics (telemetry/status/alert) and
processes them the same way as IoT Rule HTTP actions would.

Runs as a background task inside the FastAPI process. No IoT Rules required.

Topics subscribed:
  medai/device/+/telemetry
  medai/device/+/status
  medai/device/+/alert
"""
import asyncio
import json
import logging
import ssl
import threading
from pathlib import Path
from typing import Optional

import paho.mqtt.client as mqtt

from config import settings

logger = logging.getLogger(__name__)


class MQTTSubscriber:
    def __init__(self):
        self._client: Optional[mqtt.Client] = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self, loop: asyncio.AbstractEventLoop):
        """Start the MQTT client in a background thread."""
        if self._running:
            return
        if not settings.IOT_ENDPOINT:
            logger.warning("[MQTT Sub] IOT_ENDPOINT not set, skipping subscriber")
            return

        self._loop = loop
        self._running = True

        # Resolve cert paths — relative to backend/ directory
        backend_dir = Path(__file__).resolve().parent.parent
        ca_path = backend_dir / settings.IOT_CA_PATH
        cert_path = backend_dir / settings.IOT_CERT_PATH
        key_path = backend_dir / settings.IOT_KEY_PATH

        missing = [p for p in (ca_path, cert_path, key_path) if not p.exists()]
        if missing:
            logger.warning(
                f"[MQTT Sub] Missing cert files, skipping subscriber: {missing}"
            )
            self._running = False
            return

        # Use API v1 callbacks to stay compatible with paho-mqtt 1.x and 2.x
        client = mqtt.Client(
            client_id=settings.IOT_CLIENT_ID,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            if hasattr(mqtt, "CallbackAPIVersion")
            else None,
        ) if hasattr(mqtt, "CallbackAPIVersion") else mqtt.Client(
            client_id=settings.IOT_CLIENT_ID,
        )

        ctx = ssl.create_default_context()
        ctx.load_verify_locations(cafile=str(ca_path))
        ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
        ctx.check_hostname = True
        client.tls_set_context(ctx)

        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect

        self._client = client

        def run():
            try:
                logger.info(
                    f"[MQTT Sub] Connecting to {settings.IOT_ENDPOINT}:8883 "
                    f"as {settings.IOT_CLIENT_ID}"
                )
                client.connect(settings.IOT_ENDPOINT, 8883, keepalive=60)
                client.loop_forever()
            except Exception as e:
                logger.error(f"[MQTT Sub] Fatal error: {e}")
                self._running = False

        self._thread = threading.Thread(target=run, daemon=True, name="mqtt-sub")
        self._thread.start()

    def stop(self):
        if self._client:
            self._client.disconnect()
            self._client.loop_stop()
        self._running = False
        logger.info("[MQTT Sub] Stopped")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            logger.error(f"[MQTT Sub] Connection failed: rc={rc}")
            return
        logger.info("[MQTT Sub] Connected to AWS IoT Core")
        topics = [
            ("medai/device/+/telemetry", 1),
            ("medai/device/+/status", 1),
            ("medai/device/+/alert", 1),
        ]
        client.subscribe(topics)
        for t, _ in topics:
            logger.info(f"[MQTT Sub] Subscribed to {t}")

    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"[MQTT Sub] Disconnected: rc={rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception as e:
            logger.error(f"[MQTT Sub] JSON parse error on {msg.topic}: {e}")
            return

        topic_parts = msg.topic.split("/")
        if len(topic_parts) < 4:
            logger.warning(f"[MQTT Sub] Unexpected topic: {msg.topic}")
            return
        kind = topic_parts[-1]  # telemetry | status | alert

        logger.info(f"[MQTT Sub] {msg.topic} → {payload}")

        # Dispatch to async handler on the main event loop
        if self._loop and self._running:
            asyncio.run_coroutine_threadsafe(
                self._dispatch(kind, payload), self._loop
            )

    # ── Handlers (run on asyncio loop) ───────────────────────────────────────

    async def _dispatch(self, kind: str, payload: dict):
        try:
            # Import here to avoid circular imports at module load
            if kind == "telemetry":
                from routers.iot import _reconcile_inventory
                from services.dynamodb import DynamoDBService, _floats_to_decimals
                from config import settings as s
                from datetime import datetime

                device_id = payload.get("device") or payload.get("device_id")
                if not device_id:
                    return
                payload["device_id"] = device_id
                if not payload.get("timestamp"):
                    payload["timestamp"] = datetime.utcnow().isoformat() + "Z"
                payload["ttl"] = int(datetime.utcnow().timestamp()) + 7 * 86400

                db = DynamoDBService()
                table = db._table(s.DYNAMODB_TELEMETRY_TABLE)
                # DynamoDB rejects Python floats — convert temperature/humidity etc.
                table.put_item(Item=_floats_to_decimals(payload))

                inventory = payload.get("inventory") or {}
                if inventory:
                    await _reconcile_inventory(device_id, inventory)

            elif kind == "status":
                from routers.iot import _get_user_by_device
                from services.dynamodb import DynamoDBService

                device_id = payload.get("device") or payload.get("device_id")
                status = payload.get("status")
                if not device_id:
                    return
                user = await _get_user_by_device(device_id)
                if user and status == "failed":
                    db = DynamoDBService()
                    await db.create_alert({
                        "user_id": user["user_id"],
                        "medication_id": None,
                        "alert_type": "dispense_failed",
                        "severity": "warning",
                        "title": "Dispense thất bại",
                        "message": "Thiết bị báo dispense thất bại. Kiểm tra ngay.",
                    })

            elif kind == "alert":
                from routers.iot import _get_user_by_device, _format_device_alert
                from services.dynamodb import DynamoDBService
                from services.sns_service import SNSService

                device_id = payload.get("device") or payload.get("device_id")
                alert_type = payload.get("alert", "unknown")
                detail = payload.get("detail", "")
                if not device_id:
                    return
                user = await _get_user_by_device(device_id)
                if not user:
                    return

                title, message, severity = _format_device_alert(alert_type, detail)
                db = DynamoDBService()
                await db.create_alert({
                    "user_id": user["user_id"],
                    "medication_id": None,
                    "alert_type": f"device_{alert_type}",
                    "severity": severity,
                    "title": title,
                    "message": message,
                })
                if severity in ("high", "critical"):
                    sns = SNSService()
                    await sns.notify_caregiver(
                        user_id=user["user_id"],
                        subject=title,
                        message=message,
                    )
        except Exception as e:
            logger.error(f"[MQTT Sub] Dispatch error for {kind}: {e}", exc_info=True)


# Singleton
subscriber = MQTTSubscriber()
