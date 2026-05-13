"""
Setup IoT Rule -> DynamoDB for MedAI Cabinet.
Run from project root: python medai-cabinet/infrastructure/setup_iot_rule.py
"""
import boto3
import json
import os
import time
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / "backend" / ".env"
with open(env_path, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip(); v = v.strip()
        if k and v:
            os.environ.setdefault(k, v)

REGION  = os.environ.get("AWS_REGION", "ap-southeast-1")
ACCOUNT = "521330944778"
TABLE   = os.environ.get("DYNAMODB_TELEMETRY_TABLE", "medai-device-telemetry")

creds = dict(
    region_name=REGION,
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.environ.get("AWS_SESSION_TOKEN") or None,
)

iam = boto3.client("iam", **creds)
iot = boto3.client("iot", **creds)

ROLE_NAME = "medai-iot-dynamodb-role"

# ── Step 1: Create IAM role ───────────────────────────────────────────────────
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "iot.amazonaws.com"},
        "Action": "sts:AssumeRole",
    }],
}

try:
    r = iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="IoT Core role for writing telemetry to DynamoDB",
    )
    role_arn = r["Role"]["Arn"]
    print(f"[OK] Created IAM role: {role_arn}")
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]
    print(f"[OK] IAM role exists: {role_arn}")

# ── Step 2: Attach DynamoDB policy ────────────────────────────────────────────
try:
    iam.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn="arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    )
    print("[OK] Attached AmazonDynamoDBFullAccess to role")
except Exception as e:
    print(f"[WARN] Attach policy: {e}")

print("Waiting 15s for IAM role propagation...")
time.sleep(15)

# ── Step 3: Create IoT Rule → DynamoDB ───────────────────────────────────────
# SQL: extract device_id from topic path (position 3: medai/device/{device_id}/telemetry)
sql = "SELECT *, topic(3) as device_id FROM 'medai/device/+/telemetry'"

rule_payload = {
    "sql": sql,
    "description": "Write ESP32 telemetry directly to DynamoDB",
    "actions": [{
        "dynamoDBv2": {
            "roleArn": role_arn,
            "putItem": {"tableName": TABLE},
        }
    }],
    "ruleDisabled": False,
    "awsIotSqlVersion": "2016-03-23",
}

try:
    iot.create_topic_rule(
        ruleName="medai_telemetry_to_dynamo",
        topicRulePayload=rule_payload,
    )
    print("[OK] Created IoT Rule: medai_telemetry_to_dynamo")
except iot.exceptions.ResourceAlreadyExistsException:
    iot.replace_topic_rule(
        ruleName="medai_telemetry_to_dynamo",
        topicRulePayload=rule_payload,
    )
    print("[OK] Updated IoT Rule: medai_telemetry_to_dynamo")
except Exception as e:
    print(f"[FAIL] IoT Rule: {e}")
    print("-> Tao thu cong tren AWS Console theo huong dan IOT_RULES_MANUAL.md")

print("\nDone! Kiem tra tren AWS Console:")
print(f"  IoT Core -> Message routing -> Rules -> medai_telemetry_to_dynamo")
