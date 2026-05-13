"""
Expiry Service — checks medication expiry and creates alerts.
"""
import logging
from typing import List, Dict
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)


class ExpiryService:
    async def check_and_create_alerts(self, user_id: str, medication: Dict) -> List[Dict]:
        """Check a medication for expiry/low-stock issues and create alerts."""
        # Import here to avoid circular imports
        from services.dynamodb import DynamoDBService
        db = DynamoDBService()

        alerts_created = []
        med_name = medication.get("name", "Unknown")
        med_id = medication.get("medication_id", "")
        expiry_status = medication.get("expiry_status")
        days_left = medication.get("days_until_expiry")
        stock = medication.get("stock_count", 0)
        threshold = medication.get("low_stock_threshold", 5)

        # Expiry alerts
        if expiry_status == "expired":
            alert = await db.create_alert({
                "user_id": user_id,
                "medication_id": med_id,
                "alert_type": "expired",
                "severity": "critical",
                "title": f"Thuốc hết hạn: {med_name}",
                "message": f"{med_name} đã hết hạn sử dụng. Vui lòng không dùng và thay thế ngay.",
            })
            alerts_created.append(alert)

        elif expiry_status == "critical":
            alert = await db.create_alert({
                "user_id": user_id,
                "medication_id": med_id,
                "alert_type": "expiry_critical",
                "severity": "high",
                "title": f"Sắp hết hạn: {med_name}",
                "message": f"{med_name} sẽ hết hạn trong {days_left} ngày. Cần mua thêm sớm.",
            })
            alerts_created.append(alert)

        elif expiry_status == "warning":
            alert = await db.create_alert({
                "user_id": user_id,
                "medication_id": med_id,
                "alert_type": "expiry_warning",
                "severity": "medium",
                "title": f"Cảnh báo hết hạn: {med_name}",
                "message": f"{med_name} sẽ hết hạn trong {days_left} ngày.",
            })
            alerts_created.append(alert)

        # Low stock alert
        if stock <= threshold and stock > 0:
            alert = await db.create_alert({
                "user_id": user_id,
                "medication_id": med_id,
                "alert_type": "low_stock",
                "severity": "medium",
                "title": f"Sắp hết thuốc: {med_name}",
                "message": f"{med_name} chỉ còn {stock} {medication.get('unit', 'viên')}. Cần mua thêm.",
            })
            alerts_created.append(alert)

        return alerts_created
