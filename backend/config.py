from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # AWS
    AWS_REGION: str = "ap-southeast-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_SESSION_TOKEN: str = ""  # For temporary credentials (AWS Academy, SSO)

    # Cognito
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_CLIENT_ID: str = ""

    # DynamoDB
    DYNAMODB_USERS_TABLE: str = "medai-users"
    DYNAMODB_MEDICATIONS_TABLE: str = "medai-medications"
    DYNAMODB_SCHEDULES_TABLE: str = "medai-schedules"
    DYNAMODB_DOSE_HISTORY_TABLE: str = "medai-dose-history"
    DYNAMODB_ALERTS_TABLE: str = "medai-alerts"
    DYNAMODB_TELEMETRY_TABLE: str = "medai-device-telemetry"

    # S3
    S3_BUCKET_NAME: str = "medai-cabinet-images"

    # IoT
    IOT_ENDPOINT: str = ""
    IOT_CERT_PATH: str = "certs/medai-cabinet-device.cert.pem"
    IOT_KEY_PATH: str = "certs/medai-cabinet-device.private.key"
    IOT_CA_PATH: str = "certs/AmazonRootCA1.pem"
    IOT_CLIENT_ID: str = "medai-backend-server"

    # SNS
    SNS_ALERT_TOPIC_ARN: str = ""
    SNS_CAREGIVER_TOPIC_ARN: str = ""

    # Bedrock — default Llama 3 (matches .env)
    BEDROCK_MODEL_ID: str = "meta.llama3-1-8b-instruct-v1:0"
    BEDROCK_REGION: str = "us-east-1"

    # JWT
    JWT_SECRET_KEY: str = "change-this-in-production"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Expiry thresholds
    EXPIRY_WARNING_DAYS: int = 30
    EXPIRY_CRITICAL_DAYS: int = 7

    # Environment thresholds (must match firmware config.h)
    TEMP_MAX: float = 35.0       # °C
    HUMIDITY_MAX: float = 80.0   # %
    BATTERY_LOW: int = 20        # %

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
