"""
Dose Monitor — background job that detects missed doses and notifies the
caregiver through SNS.

How it works:
  Every N minutes, scans today's schedules for every user. For each scheduled
  time that is more than `MISS_THRESHOLD_MINUTES` past due AND has no matching
  dose history record, mark it as missed and notify the caregiver.

Idempotency:
  We rely on `dose-history` records as the "this dose was already handled"
  marker. When a miss is detected we insert a `status="missed"` record so
  subsequent scans skip it.
"""
import logging
from datetime import datetime, timedelta, time as dtime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from services.dynamodb import DynamoDBService
from services.sns_service import SNSService

logger = logging.getLogger(__name__)

# Vietnam = UTC+7. Schedule.times like "08:00" are interpreted in this TZ.
LOCAL_TZ = timezone(timedelta(hours=7))

# Scan interval and missed-dose threshold
SCAN_INTERVAL_MINUTES = 5
MISS_THRESHOLD_MINUTES = 30


class DoseMonitor:
    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self.db = DynamoDBService()
        self.sns = SNSService()

    def start(self):
        if self._scheduler:
            return
        self._scheduler = AsyncIOScheduler(timezone=LOCAL_TZ)
        self._scheduler.add_job(
            self._scan,
            "interval",
            minutes=SCAN_INTERVAL_MINUTES,
            id="dose_monitor_scan",
            next_run_time=datetime.now(LOCAL_TZ) + timedelta(seconds=10),
        )
        self._scheduler.start()
        logger.info(
            f"[DoseMonitor] Started (scan every {SCAN_INTERVAL_MINUTES} min, "
            f"miss threshold {MISS_THRESHOLD_MINUTES} min)"
        )

    def stop(self):
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("[DoseMonitor] Stopped")

    # ── Scan logic ────────────────────────────────────────────────────────────

    async def _scan(self):
        try:
            users = await self._list_users()
            now_local = datetime.now(LOCAL_TZ)
            today_iso = now_local.date().isoformat()

            for user in users:
                await self._scan_user(user, now_local, today_iso)
        except Exception as e:
            logger.error(f"[DoseMonitor] scan error: {e}", exc_info=True)

    async def _list_users(self) -> list[dict]:
        """Pull every user — small scan, fine for an MVP."""
        try:
            table = self.db._table(settings.DYNAMODB_USERS_TABLE)
            resp = table.scan()
            return resp.get("Items", [])
        except Exception as e:
            logger.error(f"[DoseMonitor] list_users error: {e}")
            return []

    async def _scan_user(self, user: dict, now_local: datetime, today_iso: str):
        user_id = user.get("user_id")
        if not user_id:
            return

        schedules_today = await self.db.get_today_schedule(user_id)
        if not schedules_today:
            return

        # Pull recent dose history once for this user (covers today)
        history = await self.db.list_dose_history(user_id, limit=100)
        # Build set of (medication_id, scheduled_time_iso) already handled
        handled = set()
        for h in history:
            sched_t = h.get("scheduled_time")
            if not sched_t or not sched_t.startswith(today_iso):
                continue
            mid = h.get("medication_id")
            if mid:
                handled.add((mid, sched_t))

        for entry in schedules_today:
            time_str = entry.get("time")  # "HH:MM"
            mid = entry.get("medication_id")
            if not time_str or not mid:
                continue

            try:
                hh, mm = (int(p) for p in time_str.split(":")[:2])
                scheduled_dt = now_local.replace(
                    hour=hh, minute=mm, second=0, microsecond=0
                )
            except (ValueError, AttributeError):
                continue

            # ISO with timezone
            scheduled_iso = scheduled_dt.isoformat()
            if (mid, scheduled_iso) in handled:
                continue
            # Try also a naive "today + time" key in case existing records are naive
            naive_iso = scheduled_dt.replace(tzinfo=None).isoformat()
            if (mid, naive_iso) in handled:
                continue

            # Has the deadline passed?
            minutes_late = (now_local - scheduled_dt).total_seconds() / 60
            if minutes_late < MISS_THRESHOLD_MINUTES:
                continue

            await self._mark_missed(user, entry, scheduled_dt, minutes_late)

    async def _mark_missed(
        self,
        user: dict,
        entry: dict,
        scheduled_dt: datetime,
        minutes_late: float,
    ):
        user_id = user["user_id"]
        med_name = entry.get("medication_name") or "Thuốc"
        time_str = entry.get("time")

        # Insert a missed-dose record so we don't notify twice
        try:
            await self.db.record_dose({
                "user_id": user_id,
                "medication_id": entry.get("medication_id"),
                "schedule_id": entry.get("schedule_id"),
                "scheduled_time": scheduled_dt.isoformat(),
                "status": "missed",
                "dosage_count": entry.get("dosage_count", 1),
                "notes": (
                    f"Auto-detected: {int(minutes_late)} phút trễ so với "
                    f"giờ uống {time_str}"
                ),
            })
        except Exception as e:
            logger.error(f"[DoseMonitor] record_dose missed failed: {e}")

        # Create alert + notify caregiver
        try:
            await self.db.create_alert({
                "user_id": user_id,
                "medication_id": entry.get("medication_id"),
                "alert_type": "missed_dose",
                "severity": "high",
                "title": f"Bỏ lỡ liều: {med_name}",
                "message": (
                    f"⚠️ Người dùng đã bỏ lỡ liều {med_name} "
                    f"lúc {time_str} ({int(minutes_late)} phút trước)."
                ),
            })
        except Exception as e:
            logger.error(f"[DoseMonitor] create_alert failed: {e}")

        try:
            await self.sns.notify_missed_dose(
                user_id=user_id,
                medication_name=med_name,
                scheduled_time=time_str or scheduled_dt.isoformat(),
            )
        except Exception as e:
            logger.error(f"[DoseMonitor] SNS notify failed: {e}")

        logger.info(
            f"[DoseMonitor] Missed dose logged: user={user_id} "
            f"med={med_name} time={time_str} late={int(minutes_late)}min"
        )


# Singleton
dose_monitor = DoseMonitor()
