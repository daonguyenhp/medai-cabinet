"""
MedAI Cabinet - AWS Infrastructure Setup Script
Provisions all required AWS resources using Boto3

Usage:
    # Chạy từ thư mục infrastructure/
    python aws_setup.py
    python aws_setup.py --teardown
    python aws_setup.py --create-device medai-esp32-001 --user-id demo-user-001
"""
import boto3
import json
import argparse
import time
import sys
import os
from pathlib import Path
from botocore.exceptions import ClientError

# --- Load credentials từ backend/.env ----------------------------------------
# Tìm file .env tương đối với vị trí script này
_env_path = Path(__file__).parent.parent / "backend" / ".env"

def _load_env(path: Path):
    """Parse .env file thủ công — không cần python-dotenv."""
    if not path.exists():
        print(f"[WARN]  Không tìm thấy {path}")
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value

_load_env(_env_path)

# --- Configuration ------------------------------------------------------------
APP_NAME = "medai-cabinet"
REGION   = os.environ.get("AWS_REGION", "ap-southeast-1")

DYNAMODB_TABLES = [
    {
        "TableName": "medai-users",
        "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "cognito_sub", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [{
            "IndexName": "cognito_sub-index",
            "KeySchema": [{"AttributeName": "cognito_sub", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"},
        }],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "medai-medications",
        "KeySchema": [{"AttributeName": "medication_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "medication_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [{
            "IndexName": "user_id-index",
            "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"},
        }],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "medai-schedules",
        "KeySchema": [{"AttributeName": "schedule_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "schedule_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [{
            "IndexName": "user_id-index",
            "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"},
        }],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "medai-dose-history",
        "KeySchema": [
            {"AttributeName": "history_id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "history_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "scheduled_time", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [{
            "IndexName": "user_id-scheduled_time-index",
            "KeySchema": [
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "scheduled_time", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
        }],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "medai-alerts",
        "KeySchema": [{"AttributeName": "alert_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "alert_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [{
            "IndexName": "user_id-index",
            "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"},
        }],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "medai-device-telemetry",
        "KeySchema": [
            {"AttributeName": "device_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "device_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
        "TimeToLiveSpecification": {
            "AttributeName": "ttl",
            "Enabled": True,
        },
    },
]


class MedAISetup:
    def __init__(self, region: str = REGION):
        self.region = region

        # Lấy credentials từ environment (đã load từ .env ở trên)
        creds = dict(
            region_name=region,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID") or None,
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY") or None,
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN") or None,
        )

        if not creds["aws_access_key_id"]:
            print("ERROR: Khong tim thay AWS_ACCESS_KEY_ID trong backend/.env")
            print(f"   Duong dan .env: {_env_path}")
            sys.exit(1)

        print(f"[OK] Credentials loaded (key: {creds['aws_access_key_id'][:8]}...)")
        if creds["aws_session_token"]:
            print("[OK] Session token detected (AWS Academy / temporary credentials)")

        self.dynamodb = boto3.client("dynamodb", **creds)
        self.s3       = boto3.client("s3",           **creds)
        self.iot      = boto3.client("iot",          **creds)
        self.cognito  = boto3.client("cognito-idp",  **creds)
        self.sns      = boto3.client("sns",          **creds)
        self.iam      = boto3.client("iam",          **creds)
        self.resources = {}

    def setup_all(self):
        """Provision all AWS resources."""
        print(f"\n{'='*60}")
        print(f"  MedAI Cabinet - AWS Setup ({self.region})")
        print(f"{'='*60}\n")

        # Verify credentials are valid before proceeding
        self._verify_credentials()

        self.setup_dynamodb()
        self.setup_s3()
        self.setup_cognito()
        self.setup_sns()
        self.setup_iot()
        self.setup_iot_rules()

        print("\n[OK] All resources provisioned successfully!")
        self._print_summary()

    def _verify_credentials(self):
        """Quick check that credentials are valid and not expired."""
        try:
            sts = boto3.client(
                "sts",
                region_name=self.region,
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.environ.get("AWS_SESSION_TOKEN") or None,
            )
            identity = sts.get_caller_identity()
            print(f"[OK] AWS Identity: Account={identity['Account']}, "
                  f"UserId={identity['UserId'][:20]}...")
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("ExpiredTokenException", "InvalidClientTokenId"):
                print("\n[ERROR] AWS credentials da het han hoac khong hop le!")
                print("  Neu dung AWS Academy:")
                print("  1. Vao https://awsacademy.instructure.com")
                print("  2. Mo Lab -> Click 'Start Lab' (cho den khi xanh)")
                print("  3. Click 'AWS Details' -> Copy 3 dong credentials")
                print("  4. Dan vao backend/.env:")
                print("     AWS_ACCESS_KEY_ID=...")
                print("     AWS_SECRET_ACCESS_KEY=...")
                print("     AWS_SESSION_TOKEN=...")
                print("  5. Chay lai: python aws_setup.py")
                sys.exit(1)
            raise

    def setup_dynamodb(self):
        """Create DynamoDB tables."""
        print("[DynamoDB] Setting up DynamoDB tables...")
        for table_config in DYNAMODB_TABLES:
            table_name = table_config["TableName"]
            try:
                # Check if table exists
                self.dynamodb.describe_table(TableName=table_name)
                print(f"  [OK] Table already exists: {table_name}")
            except ClientError as e:
                code = e.response["Error"]["Code"]
                if code == "ExpiredTokenException":
                    print("\n[ERROR] AWS session token da het han!")
                    print("  -> Vao AWS Academy -> Start Lab -> Copy credentials moi")
                    print("  -> Cap nhat backend/.env roi chay lai script")
                    sys.exit(1)
                elif code == "ResourceNotFoundException":
                    config = {k: v for k, v in table_config.items() if k != "TimeToLiveSpecification"}
                    self.dynamodb.create_table(**config)
                    print(f"  + Created table: {table_name}")

                    # Wait for table to be active
                    waiter = self.dynamodb.get_waiter("table_exists")
                    waiter.wait(TableName=table_name)

                    # Enable TTL if specified
                    if "TimeToLiveSpecification" in table_config:
                        self.dynamodb.update_time_to_live(
                            TableName=table_name,
                            TimeToLiveSpecification=table_config["TimeToLiveSpecification"],
                        )
                else:
                    raise

        # Enable point-in-time recovery for critical tables
        for table_name in ["medai-medications", "medai-dose-history"]:
            try:
                self.dynamodb.update_continuous_backups(
                    TableName=table_name,
                    PointInTimeRecoverySpecification={"PointInTimeRecoveryEnabled": True},
                )
                print(f"  [OK] PITR enabled: {table_name}")
            except ClientError:
                pass

    def setup_s3(self):
        """Create S3 bucket for images."""
        print("\n[S3] Setting up S3 bucket...")
        bucket_name = f"{APP_NAME}-images-{self.region}"
        try:
            if self.region == "us-east-1":
                self.s3.create_bucket(Bucket=bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": self.region},
                )
            print(f"  + Created bucket: {bucket_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] in ["BucketAlreadyOwnedByYou", "BucketAlreadyExists"]:
                print(f"  [OK] Bucket already exists: {bucket_name}")
            else:
                raise

        # Block public access
        self.s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )

        # Enable versioning
        self.s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={"Status": "Enabled"},
        )

        # Lifecycle rule: delete captures after 30 days
        self.s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={
                "Rules": [{
                    "ID": "delete-old-captures",
                    "Status": "Enabled",
                    "Filter": {"Prefix": "captures/"},
                    "Expiration": {"Days": 30},
                }]
            },
        )

        # Enable server-side encryption
        self.s3.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            },
        )

        self.resources["s3_bucket"] = bucket_name
        print(f"  [OK] S3 bucket configured: {bucket_name}")

    def setup_cognito(self):
        """Create Cognito User Pool."""
        print("\n[Cognito] Setting up Cognito User Pool...")
        pool_name = f"{APP_NAME}-users"

        try:
            response = self.cognito.create_user_pool(
                PoolName=pool_name,
                Policies={
                    "PasswordPolicy": {
                        "MinimumLength": 8,
                        "RequireUppercase": False,
                        "RequireLowercase": True,
                        "RequireNumbers": True,
                        "RequireSymbols": False,
                    }
                },
                AutoVerifiedAttributes=["phone_number"],
                UsernameAttributes=["phone_number"],
                SmsConfiguration={
                    "SnsCallerArn": "arn:aws:iam::ACCOUNT_ID:role/CognitoSNSRole",
                    "ExternalId": "medai-cognito",
                },
                UserPoolTags={"Project": APP_NAME},
                AccountRecoverySetting={
                    "RecoveryMechanisms": [{"Priority": 1, "Name": "verified_phone_number"}]
                },
            )
            pool_id = response["UserPool"]["Id"]
            print(f"  + Created User Pool: {pool_id}")

            # Create app client
            client_response = self.cognito.create_user_pool_client(
                UserPoolId=pool_id,
                ClientName=f"{APP_NAME}-app",
                GenerateSecret=False,
                ExplicitAuthFlows=[
                    "ALLOW_USER_PASSWORD_AUTH",
                    "ALLOW_REFRESH_TOKEN_AUTH",
                    "ALLOW_USER_SRP_AUTH",
                ],
                TokenValidityUnits={
                    "AccessToken": "hours",
                    "IdToken": "hours",
                    "RefreshToken": "days",
                },
                AccessTokenValidity=1,
                IdTokenValidity=1,
                RefreshTokenValidity=30,
            )
            client_id = client_response["UserPoolClient"]["ClientId"]
            self.resources["cognito_pool_id"] = pool_id
            self.resources["cognito_client_id"] = client_id
            print(f"  + Created App Client: {client_id}")

        except ClientError as e:
            print(f"  [WARN] Cognito setup: {e.response['Error']['Message']}")

    def setup_sns(self):
        """Create SNS topics for alerts."""
        print("\n[SNS] Setting up SNS topics...")
        topics = [
            ("medai-alerts", "MedAI Cabinet Alerts"),
            ("medai-caregiver", "MedAI Caregiver Notifications"),
        ]
        for topic_name, display_name in topics:
            try:
                response = self.sns.create_topic(
                    Name=topic_name,
                    Attributes={"DisplayName": display_name},
                    Tags=[{"Key": "Project", "Value": APP_NAME}],
                )
                arn = response["TopicArn"]
                self.resources[f"sns_{topic_name}"] = arn
                print(f"  + Created SNS topic: {topic_name} ({arn})")
            except ClientError as e:
                print(f"  [WARN] SNS: {e.response['Error']['Message']}")

    def setup_iot(self):
        """Create IoT Thing Type and Policy."""
        print("\n[IoT] Setting up AWS IoT Core...")

        # Create Thing Type
        try:
            self.iot.create_thing_type(
                thingTypeName="medai-cabinet",
                thingTypeProperties={
                    "thingTypeDescription": "MedAI Cabinet ESP32 Device",
                    "searchableAttributes": ["location", "user_id"],
                },
            )
            print("  + Created Thing Type: medai-cabinet")
        except ClientError as e:
            if "ResourceAlreadyExistsException" not in str(e):
                print(f"  [WARN] Thing Type: {e}")

        # Create IoT Policy
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["iot:Connect"],
                    "Resource": f"arn:aws:iot:{self.region}:*:client/medai-*",
                },
                {
                    "Effect": "Allow",
                    "Action": ["iot:Publish"],
                    "Resource": [
                        f"arn:aws:iot:{self.region}:*:topic/medai/device/*/telemetry",
                        f"arn:aws:iot:{self.region}:*:topic/medai/device/*/status",
                        f"arn:aws:iot:{self.region}:*:topic/medai/device/*/heartbeat",
                    ],
                },
                {
                    "Effect": "Allow",
                    "Action": ["iot:Subscribe", "iot:Receive"],
                    "Resource": [
                        f"arn:aws:iot:{self.region}:*:topicfilter/medai/device/*/command",
                        f"arn:aws:iot:{self.region}:*:topic/medai/device/*/command",
                    ],
                },
                {
                    "Effect": "Allow",
                    "Action": ["iot:GetThingShadow", "iot:UpdateThingShadow"],
                    "Resource": f"arn:aws:iot:{self.region}:*:thing/medai-*",
                },
            ],
        }

        try:
            self.iot.create_policy(
                policyName="medai-device-policy",
                policyDocument=json.dumps(policy_document),
            )
            print("  + Created IoT Policy: medai-device-policy")
        except ClientError as e:
            if "ResourceAlreadyExistsException" not in str(e):
                print(f"  [WARN] IoT Policy: {e}")

    def setup_iot_rules(self):
        """
        Create IoT Rules — write telemetry directly to DynamoDB.

        AWS Academy does NOT allow IoT Rules with HTTP actions (cross-account role).
        Solution: IoT Rule writes directly to DynamoDB table.
        Backend reads from DynamoDB (polling) instead of receiving webhooks.
        """
        print("\n[Rules] Setting up IoT Rules (DynamoDB direct write)...")

        account_id = self._get_account_id()
        table_name = os.environ.get("DYNAMODB_TELEMETRY_TABLE", "medai-device-telemetry")

        # IAM role for IoT → DynamoDB (AWS Academy provides LabRole)
        # Try common role names used in AWS Academy
        role_arn = None
        for role_name in ["medai-iot-dynamodb-role", "LabRole", "EMR_EC2_DefaultRole", "AWSServiceRoleForIoT"]:
            try:
                resp = self.iam.get_role(RoleName=role_name)
                role_arn = resp["Role"]["Arn"]
                print(f"  [OK] Using IAM role: {role_name} ({role_arn})")
                break
            except ClientError:
                continue

        if not role_arn:
            print("  [WARN] Khong tim thay IAM role phu hop.")
            print("  -> IoT Rules se duoc tao thu cong tren AWS Console.")
            print("  -> Xem huong dan: infrastructure/IOT_RULES_MANUAL.md")
            self._write_iot_rules_manual(account_id, table_name)
            return

        # Rule: telemetry → DynamoDB
        telemetry_rule = {
            "sql": f"SELECT *, topic(3) as device_id, timestamp() as ts "
                   f"FROM 'medai/device/+/telemetry'",
            "description": "Write device telemetry to DynamoDB",
            "actions": [{
                "dynamoDBv2": {
                    "roleArn": role_arn,
                    "putItem": {"tableName": table_name},
                }
            }],
            "ruleDisabled": False,
            "awsIotSqlVersion": "2016-03-23",
        }

        for rule_name, payload in [("medai_telemetry_to_dynamo", telemetry_rule)]:
            try:
                self.iot.create_topic_rule(
                    ruleName=rule_name,
                    topicRulePayload=payload,
                )
                print(f"  + Created IoT Rule: {rule_name}")
            except ClientError as e:
                code = e.response["Error"]["Code"]
                if "ResourceAlreadyExistsException" in str(e):
                    print(f"  [OK] Rule already exists: {rule_name}")
                else:
                    print(f"  [WARN] Rule {rule_name}: {e.response['Error']['Message']}")
                    print("  -> Tao thu cong tren AWS Console (xem IOT_RULES_MANUAL.md)")
                    self._write_iot_rules_manual(account_id, table_name)

    def _get_account_id(self) -> str:
        try:
            sts = boto3.client(
                "sts",
                region_name=self.region,
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.environ.get("AWS_SESSION_TOKEN") or None,
            )
            return sts.get_caller_identity()["Account"]
        except Exception:
            return "521330944778"

    def _write_iot_rules_manual(self, account_id: str, table_name: str):
        """Write manual IoT Rules setup guide."""
        content = f"""# Tao IoT Rules thu cong tren AWS Console

## Buoc 1 — Mo AWS Console
Vao: IoT Core -> Message routing -> Rules -> Create rule

## Rule 1: medai_telemetry_to_dynamo
- Rule name: medai_telemetry_to_dynamo
- SQL:
  SELECT *, topic(3) as device_id, timestamp() as ts
  FROM 'medai/device/+/telemetry'
- Action: DynamoDBv2
  - Table name: {table_name}
  - IAM role: LabRole (hoac tao role moi voi policy AmazonDynamoDBFullAccess)

## Rule 2: medai_status_to_dynamo (optional)
- Rule name: medai_status_to_dynamo
- SQL: SELECT *, topic(3) as device_id FROM 'medai/device/+/status'
- Action: DynamoDBv2 -> Table: {table_name}
  (dung chung bang telemetry, them field "type": "status")

## Luu y
- AWS Academy chi cho phep DynamoDB/SNS/S3 actions trong IoT Rules
- HTTP action bi chan do cross-account role restriction
- Backend se poll DynamoDB de lay telemetry (khong can webhook)
"""
        guide_path = Path(__file__).parent / "IOT_RULES_MANUAL.md"
        guide_path.write_text(content, encoding="utf-8")
        print(f"  -> Huong dan da luu tai: {guide_path}")

    def create_device(self, device_id: str, user_id: str, location: str = ""):
        """Register a new ESP32 device in IoT Core."""
        print(f"\n[SNS] Registering device: {device_id}")

        # Create Thing
        self.iot.create_thing(
            thingName=device_id,
            thingTypeName="medai-cabinet",
            attributePayload={
                "attributes": {"user_id": user_id, "location": location},
                "merge": False,
            },
        )

        # Create certificate
        cert_response = self.iot.create_keys_and_certificate(setAsActive=True)
        cert_arn = cert_response["certificateArn"]
        cert_id = cert_response["certificateId"]

        # Attach policy
        self.iot.attach_policy(policyName="medai-device-policy", target=cert_arn)

        # Attach certificate to thing
        self.iot.attach_thing_principal(thingName=device_id, principal=cert_arn)

        print(f"  [OK] Device registered: {device_id}")
        print(f"  [OK] Certificate ID: {cert_id}")
        print("\n  [WARN]  Save these certificates securely - they cannot be retrieved again!")

        return {
            "device_id": device_id,
            "certificate_id": cert_id,
            "certificate_pem": cert_response["certificatePem"],
            "private_key": cert_response["keyPair"]["PrivateKey"],
            "public_key": cert_response["keyPair"]["PublicKey"],
        }

    def _print_summary(self):
        print(f"\n{'='*60}")
        print("  Resource Summary")
        print(f"{'='*60}")
        for key, value in self.resources.items():
            print(f"  {key}: {value}")
        print(f"\n  Update your .env file with these values!")
        print(f"{'='*60}\n")

    def teardown(self):
        """Remove all provisioned resources (use with caution!)."""
        print("\n[WARN]  TEARDOWN - This will delete all MedAI Cabinet resources!")
        confirm = input("Type 'DELETE' to confirm: ")
        if confirm != "DELETE":
            print("Cancelled.")
            return

        # Delete DynamoDB tables
        for table in DYNAMODB_TABLES:
            try:
                self.dynamodb.delete_table(TableName=table["TableName"])
                print(f"  - Deleted table: {table['TableName']}")
            except ClientError:
                pass

        print("Teardown complete.")


def main():
    parser = argparse.ArgumentParser(description="MedAI Cabinet AWS Setup")
    parser.add_argument("--region", default=REGION, help=f"AWS region (default: {REGION})")
    parser.add_argument("--teardown", action="store_true", help="Remove all resources")
    parser.add_argument("--create-device", metavar="DEVICE_ID", help="Register a new device")
    parser.add_argument("--user-id", help="User ID for device registration")
    args = parser.parse_args()

    print(f"Region: {args.region}")
    print(f".env:   {_env_path}")

    setup = MedAISetup(region=args.region)

    if args.teardown:
        setup.teardown()
    elif args.create_device:
        if not args.user_id:
            print("Error: --user-id required for device registration")
            sys.exit(1)
        certs = setup.create_device(args.create_device, args.user_id)
        # Save certificates to files
        with open(f"{args.create_device}-cert.pem", "w") as f:
            f.write(certs["certificate_pem"])
        with open(f"{args.create_device}-private.key", "w") as f:
            f.write(certs["private_key"])
        print(f"\n  Certificates saved to {args.create_device}-cert.pem and {args.create_device}-private.key")
    else:
        setup.setup_all()


if __name__ == "__main__":
    main()
