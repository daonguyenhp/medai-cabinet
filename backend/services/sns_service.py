"""
SNS Service — sends notifications to patients and caregivers.
"""
import boto3
import logging
from config import settings

logger = logging.getLogger(__name__)


class SNSService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "sns",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
                aws_session_token=settings.AWS_SESSION_TOKEN or None,
            )
        return self._client

    async def notify_alert(self, subject: str, message: str):
        """Publish to the general alerts topic."""
        if not settings.SNS_ALERT_TOPIC_ARN:
            logger.debug("SNS_ALERT_TOPIC_ARN not configured, skipping")
            return
        try:
            self.client.publish(
                TopicArn=settings.SNS_ALERT_TOPIC_ARN,
                Subject=subject[:100],
                Message=message,
            )
            logger.info(f"SNS alert sent: {subject}")
        except Exception as e:
            logger.error(f"SNS notify_alert error: {e}")

    async def notify_caregiver(self, user_id: str, subject: str, message: str):
        """Publish to the caregiver topic."""
        if not settings.SNS_CAREGIVER_TOPIC_ARN:
            logger.debug("SNS_CAREGIVER_TOPIC_ARN not configured, skipping")
            return
        try:
            full_message = f"[MedAI Cabinet] Người dùng: {user_id}\n\n{message}"
            self.client.publish(
                TopicArn=settings.SNS_CAREGIVER_TOPIC_ARN,
                Subject=f"[MedAI] {subject[:90]}",
                Message=full_message,
            )
            logger.info(f"SNS caregiver notification sent for user {user_id}")
        except Exception as e:
            logger.error(f"SNS notify_caregiver error: {e}")

    async def notify_missed_dose(self, user_id: str, medication_name: str, scheduled_time: str):
        """Notify caregiver when a dose is missed."""
        subject = f"Bỏ lỡ liều thuốc: {medication_name}"
        message = (
            f"⚠️ Người dùng {user_id} đã bỏ lỡ liều thuốc {medication_name} "
            f"lúc {scheduled_time}.\n\nVui lòng kiểm tra và nhắc nhở."
        )
        await self.notify_caregiver(user_id=user_id, subject=subject, message=message)
        await self.notify_alert(subject=subject, message=message)
