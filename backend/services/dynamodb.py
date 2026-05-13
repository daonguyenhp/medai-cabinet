"""
DynamoDB service — wraps all database operations for MedAI Cabinet.
"""
import boto3
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from boto3.dynamodb.conditions import Key, Attr

from config import settings

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _compute_expiry_status(expiry_date_str: Optional[str], post_opening_days: Optional[int],
                            opened_date_str: Optional[str]) -> Dict[str, Any]:
    """Compute expiry status and days until expiry."""
    today = date.today()
    effective_expiry = None

    if expiry_date_str:
        try:
            effective_expiry = date.fromisoformat(expiry_date_str)
        except ValueError:
            pass

    if post_opening_days and opened_date_str:
        try:
            opened = date.fromisoformat(opened_date_str)
            post_open_expiry = opened + timedelta(days=post_opening_days)
            if effective_expiry is None or post_open_expiry < effective_expiry:
                effective_expiry = post_open_expiry
        except ValueError:
            pass

    if effective_expiry is None:
        return {"expiry_status": "unknown", "days_until_expiry": None, "effective_expiry_date": None, "warning_message": None}

    days_left = (effective_expiry - today).days

    if days_left < 0:
        status = "expired"
        msg = f"Đã hết hạn {abs(days_left)} ngày trước"
    elif days_left <= settings.EXPIRY_CRITICAL_DAYS:
        status = "critical"
        msg = f"Hết hạn trong {days_left} ngày!"
    elif days_left <= settings.EXPIRY_WARNING_DAYS:
        status = "warning"
        msg = f"Hết hạn trong {days_left} ngày"
    else:
        status = "ok"
        msg = None

    return {
        "expiry_status": status,
        "days_until_expiry": days_left,
        "effective_expiry_date": effective_expiry.isoformat(),
        "warning_message": msg,
    }


class DynamoDBService:
    def __init__(self):
        self._dynamodb = None

    @property
    def dynamodb(self):
        if self._dynamodb is None:
            self._dynamodb = boto3.resource(
                "dynamodb",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
                aws_session_token=settings.AWS_SESSION_TOKEN or None,
            )
        return self._dynamodb

    def _table(self, name: str):
        return self.dynamodb.Table(name)

    # ── Users ──────────────────────────────────────────────────────────────────

    async def get_user(self, user_id: str) -> Optional[Dict]:
        try:
            resp = self._table(settings.DYNAMODB_USERS_TABLE).get_item(Key={"user_id": user_id})
            return resp.get("Item")
        except Exception as e:
            logger.error(f"get_user error: {e}")
            return None

    async def get_user_device(self, user_id: str) -> Optional[str]:
        user = await self.get_user(user_id)
        return user.get("device_id") if user else None

    # ── Medications ────────────────────────────────────────────────────────────

    async def list_medications(self, user_id: str) -> List[Dict]:
        try:
            table = self._table(settings.DYNAMODB_MEDICATIONS_TABLE)
            resp = table.query(
                IndexName="user_id-index",
                KeyConditionExpression=Key("user_id").eq(user_id)
            )
            items = resp.get("Items", [])
            for item in items:
                expiry_info = _compute_expiry_status(
                    item.get("expiry_date"),
                    item.get("post_opening_days"),
                    item.get("opened_date"),
                )
                item.update(expiry_info)
            return items
        except Exception as e:
            logger.error(f"list_medications error: {e}")
            return []

    async def get_medication(self, medication_id: str) -> Optional[Dict]:
        try:
            resp = self._table(settings.DYNAMODB_MEDICATIONS_TABLE).get_item(
                Key={"medication_id": medication_id}
            )
            item = resp.get("Item")
            if item:
                expiry_info = _compute_expiry_status(
                    item.get("expiry_date"),
                    item.get("post_opening_days"),
                    item.get("opened_date"),
                )
                item.update(expiry_info)
            return item
        except Exception as e:
            logger.error(f"get_medication error: {e}")
            return None

    async def create_medication(self, data: Dict) -> Dict:
        data["medication_id"] = str(uuid.uuid4())
        data["created_at"] = _now_iso()
        data["updated_at"] = _now_iso()
        self._table(settings.DYNAMODB_MEDICATIONS_TABLE).put_item(Item=data)
        expiry_info = _compute_expiry_status(
            data.get("expiry_date"), data.get("post_opening_days"), data.get("opened_date")
        )
        data.update(expiry_info)
        return data

    async def update_medication(self, medication_id: str, updates: Dict) -> Dict:
        updates["updated_at"] = _now_iso()
        table = self._table(settings.DYNAMODB_MEDICATIONS_TABLE)

        update_expr = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
        expr_names = {f"#{k}": k for k in updates}
        expr_values = {f":{k}": v for k, v in updates.items()}

        resp = table.update_item(
            Key={"medication_id": medication_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
        )
        item = resp.get("Attributes", {})
        expiry_info = _compute_expiry_status(
            item.get("expiry_date"), item.get("post_opening_days"), item.get("opened_date")
        )
        item.update(expiry_info)
        return item

    async def delete_medication(self, medication_id: str):
        self._table(settings.DYNAMODB_MEDICATIONS_TABLE).delete_item(
            Key={"medication_id": medication_id}
        )

    # ── Schedules ──────────────────────────────────────────────────────────────

    async def list_schedules(self, user_id: str) -> List[Dict]:
        try:
            table = self._table(settings.DYNAMODB_SCHEDULES_TABLE)
            resp = table.query(
                IndexName="user_id-index",
                KeyConditionExpression=Key("user_id").eq(user_id)
            )
            return resp.get("Items", [])
        except Exception as e:
            logger.error(f"list_schedules error: {e}")
            return []

    async def create_schedule(self, data: Dict) -> Dict:
        data["schedule_id"] = str(uuid.uuid4())
        data["created_at"] = _now_iso()
        self._table(settings.DYNAMODB_SCHEDULES_TABLE).put_item(Item=data)
        return data

    async def delete_schedule(self, schedule_id: str):
        self._table(settings.DYNAMODB_SCHEDULES_TABLE).delete_item(
            Key={"schedule_id": schedule_id}
        )

    async def get_today_schedule(self, user_id: str) -> List[Dict]:
        schedules = await self.list_schedules(user_id)
        today = date.today().strftime("%A").lower()
        result = []
        for sched in schedules:
            if not sched.get("is_active"):
                continue
            if today not in sched.get("days_of_week", []):
                continue
            med = await self.get_medication(sched.get("medication_id", ""))
            for t in sched.get("times", []):
                result.append({
                    "schedule_id": sched["schedule_id"],
                    "medication_id": sched.get("medication_id"),
                    "medication_name": med.get("name") if med else "Unknown",
                    "unit": med.get("unit", "viên") if med else "viên",
                    "time": t,
                    "dosage_count": sched.get("dosage_count", 1),
                    "instructions": sched.get("instructions"),
                    "status": "pending",
                })
        result.sort(key=lambda x: x["time"])
        return result

    # ── Dose History ───────────────────────────────────────────────────────────

    async def record_dose(self, data: Dict) -> Dict:
        data["history_id"] = str(uuid.uuid4())
        data["created_at"] = _now_iso()
        if not data.get("taken_time"):
            data["taken_time"] = _now_iso()
        self._table(settings.DYNAMODB_DOSE_HISTORY_TABLE).put_item(Item=data)
        return data

    async def list_dose_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        try:
            table = self._table(settings.DYNAMODB_DOSE_HISTORY_TABLE)
            resp = table.query(
                IndexName="user_id-index",
                KeyConditionExpression=Key("user_id").eq(user_id),
                ScanIndexForward=False,
                Limit=limit,
            )
            return resp.get("Items", [])
        except Exception as e:
            logger.error(f"list_dose_history error: {e}")
            return []

    # ── Alerts ─────────────────────────────────────────────────────────────────

    async def list_alerts(self, user_id: str, resolved: Optional[bool] = None) -> List[Dict]:
        try:
            table = self._table(settings.DYNAMODB_ALERTS_TABLE)
            resp = table.query(
                IndexName="user_id-index",
                KeyConditionExpression=Key("user_id").eq(user_id),
                ScanIndexForward=False,
            )
            items = resp.get("Items", [])
            if resolved is not None:
                items = [i for i in items if i.get("resolved", False) == resolved]
            return items
        except Exception as e:
            logger.error(f"list_alerts error: {e}")
            return []

    async def create_alert(self, data: Dict) -> Dict:
        data["alert_id"] = str(uuid.uuid4())
        data["created_at"] = _now_iso()
        data["resolved"] = False
        self._table(settings.DYNAMODB_ALERTS_TABLE).put_item(Item=data)
        return data

    async def resolve_alert(self, alert_id: str):
        self._table(settings.DYNAMODB_ALERTS_TABLE).update_item(
            Key={"alert_id": alert_id},
            UpdateExpression="SET resolved = :r, resolved_at = :t",
            ExpressionAttributeValues={":r": True, ":t": _now_iso()},
        )

    # ── Device Telemetry ───────────────────────────────────────────────────────

    async def get_latest_telemetry(self, device_id: str) -> Optional[Dict]:
        try:
            table = self._table(settings.DYNAMODB_TELEMETRY_TABLE)
            resp = table.query(
                KeyConditionExpression=Key("device_id").eq(device_id),
                ScanIndexForward=False,
                Limit=1,
            )
            items = resp.get("Items", [])
            return items[0] if items else None
        except Exception as e:
            logger.error(f"get_latest_telemetry error: {e}")
            return None

    async def get_telemetry_history(self, device_id: str, hours: int = 24) -> List[Dict]:
        try:
            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
            table = self._table(settings.DYNAMODB_TELEMETRY_TABLE)
            resp = table.query(
                KeyConditionExpression=Key("device_id").eq(device_id) & Key("timestamp").gte(cutoff),
                ScanIndexForward=False,
            )
            return resp.get("Items", [])
        except Exception as e:
            logger.error(f"get_telemetry_history error: {e}")
            return []

    async def list_devices(self, user_id: str) -> List[Dict]:
        user = await self.get_user(user_id)
        if not user or not user.get("device_id"):
            return []
        telemetry = await self.get_latest_telemetry(user["device_id"])
        return [{
            "device_id": user["device_id"],
            "status": "online" if telemetry else "offline",
            "last_seen": telemetry.get("timestamp") if telemetry else None,
            "telemetry": telemetry,
        }]
